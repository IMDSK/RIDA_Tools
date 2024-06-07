import os
import shutil
import logging
from concurrent.futures import ThreadPoolExecutor
import subprocess
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window
from shapely.geometry import box
import numpy as np

logger = logging.getLogger()

# FullyTile --------------------------------------------------------------------------------------------------------------------------------------------------------------------

def resample_raster(input_raster, output_raster, new_resolution):
    try:
        with rasterio.open(input_raster) as src:
            transform = src.transform
            data = src.read(
                out_shape=(
                    src.count,
                    int(src.height * src.transform.a / new_resolution),
                    int(src.width * src.transform.a / new_resolution)
                ),
                resampling=Resampling.nearest
            )
            transform = src.transform * src.transform.scale(
                (src.width / data.shape[-1]),
                (src.height / data.shape[-2])
            )
            profile = src.profile
            profile.update(transform=transform, width=data.shape[2], height=data.shape[1])

            with rasterio.open(output_raster, 'w', **profile) as dst:
                dst.write(data)
        logger.info(f"Resampled raster saved to {output_raster}")
    except Exception as e:
        logger.error(f"Failed to resample raster {input_raster}: {e}")

def parallel_resample(raster_pairs):
    with ThreadPoolExecutor() as executor:
        executor.map(lambda pair: resample_raster(pair[0], pair[1], pair[2]), raster_pairs)

def chop_and_save_tiles(cropped_raster, meta, tile_size, output_folder, original_filename):
    try:
        if meta['width'] <= tile_size and meta['height'] <= tile_size:
            logger.info(f"Image {original_filename} is smaller than the tile size; skipping chop.")
            area_folder_path = os.path.join(output_folder, "Area00")
            if not os.path.exists(area_folder_path):
                os.makedirs(area_folder_path)

            tile_name = f"{original_filename}.jp2"
            tile_path = os.path.join(area_folder_path, tile_name)

            with rasterio.open(tile_path, "w", **meta) as tile_raster:
                tile_raster.write(cropped_raster.read())
            logger.info(f"Saved entire image {tile_name} to {area_folder_path}")
            return

        bounds = cropped_raster.bounds
        left, bottom, right, top = bounds

        tile_width = (meta['width'] + tile_size - 1) // tile_size
        tile_height = (meta['height'] + tile_size - 1) // tile_size

        for row in range(tile_height):
            for col in range(tile_width):
                window = Window(col * tile_size, row * tile_size, tile_size, tile_size)
                tile_data = cropped_raster.read(window=window)

                if tile_data.any():
                    x_min = left + col * tile_size * meta['transform'][0]
                    y_max = top + row * tile_size * meta['transform'][3]
                    x_max = x_min + tile_size * meta['transform'][0]
                    y_min = y_max + tile_size * meta['transform'][3]
                    tile_bounds = box(x_min, y_min, x_max, y_min)

                    area_folder = f"Area{row}{col}"
                    area_folder_path = os.path.join(output_folder, area_folder)
                    if not os.path.exists(area_folder_path):
                        os.makedirs(area_folder_path)

                    tile_name = f"{original_filename}.jp2"
                    tile_path = os.path.join(area_folder_path, tile_name)
                    tile_meta = meta.copy()
                    tile_meta.update({
                        "height": tile_size,
                        "width": tile_size,
                        "transform": rasterio.transform.from_bounds(*tile_bounds.bounds, tile_size, tile_size)
                    })

                    with rasterio.open(tile_path, "w", **tile_meta) as tile_raster:
                        tile_raster.write(tile_data)
                    logger.info(f"Saved tile {tile_name} to {area_folder_path}")
    except Exception as e:
        logger.error(f"Failed to save tiles for {original_filename}: {e}")

def rename_file(original_name, folder_type):
    parts = original_name.split('_')
    if '20m' in original_name or '60m' in original_name:
        if 'B12' in original_name and folder_type == 'Before':
            new_name = f"{parts[0]}_B1210.jp2"
        else:
            parts[-2] = parts[-2].replace('20m', '10').replace('60m', '10')
            new_name = f"{parts[0]}_{parts[1]}_{parts[2]}10.jp2"
    elif folder_type == 'Before':
        new_name = f"{parts[0]}_{parts[2]}.jp2"
    else:  
        new_name = f"{parts[0]}_{parts[1]}_{parts[2]}.jp2"  
    return new_name

def process_files(folder_path, output_folder_pre, output_folder_after, config=None):
    before_path = os.path.join(folder_path, 'Before')
    after_path = os.path.join(folder_path, 'After')

    if not os.path.exists(before_path) or not os.path.exists(after_path):
        logger.error("Required 'Before' and 'After' folders are not found.")
        return

    before_jp2_files = [f for f in os.listdir(before_path) if f.endswith(".jp2")]
    after_jp2_files = [f for f in os.listdir(after_path) if f.endswith(".jp2")]

    # Ensure "Before" folder has required files
    required_files = ['_B08_10m.jp2', '_B12_20m.jp2']
    if not all(any(req_file in file for file in before_jp2_files) for req_file in required_files):
        logger.error("Required files are missing in 'Before' folder.")
        return

    prepare_dir_before = './prepare_image/Before'
    prepare_dir_after = './prepare_image/After'
    rename_dir_before = './rename_image/Before'
    rename_dir_after = './rename_image/After'
    
    # Create directories if they don't exist
    for directory in [prepare_dir_before, prepare_dir_after, rename_dir_before, rename_dir_after]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Copy all files to the prepare_image directory
    for filename in before_jp2_files:
        shutil.copy(os.path.join(before_path, filename), os.path.join(prepare_dir_before, filename))

    for filename in after_jp2_files:
        shutil.copy(os.path.join(after_path, filename), os.path.join(prepare_dir_after, filename))

    logger.info("Files copied to prepare_image directory.")

    resample_needed = [("20m", 10), ("60m", 10)]
    resample_pairs = []

    for filename in before_jp2_files:
        if any(res in filename for res, _ in resample_needed):
            resolution = next(new_res for res, new_res in resample_needed if res in filename)
            resampled_filename = rename_file(filename, 'Before')
            resample_pairs.append((os.path.join(prepare_dir_before, filename), os.path.join(rename_dir_before, resampled_filename), resolution))

    for filename in after_jp2_files:
        if any(res in filename for res, _ in resample_needed):
            resolution = next(new_res for res, new_res in resample_needed if res in filename)
            resampled_filename = rename_file(filename, 'After')
            resample_pairs.append((os.path.join(prepare_dir_after, filename), os.path.join(rename_dir_after, resampled_filename), resolution))

    parallel_resample(resample_pairs)

    # Move and rename non-resampled files to rename_dir
    for filename in before_jp2_files:
        if not any(res in filename for res, _ in resample_needed):
            new_filename = rename_file(filename, 'Before')
            shutil.copy(os.path.join(prepare_dir_before, filename), os.path.join(rename_dir_before, new_filename))

    for filename in after_jp2_files:
        if not any(res in filename for res, _ in resample_needed):
            new_filename = rename_file(filename, 'After')
            shutil.copy(os.path.join(prepare_dir_after, filename), os.path.join(rename_dir_after, new_filename))

    all_files_before = [rename_file(f, 'Before') if any(res in f for res, _ in resample_needed) else rename_file(f, 'Before') for f in before_jp2_files]
    all_files_after = [rename_file(f, 'After') if any(res in f for res, _ in resample_needed) else rename_file(f, 'After') for f in after_jp2_files]

    all_files_before = [os.path.basename(f) for f in all_files_before]
    all_files_after = [os.path.basename(f) for f in all_files_after]

    # Ensure unique filenames
    unique_files_before = {os.path.basename(f): f for f in all_files_before}.values()
    unique_files_after = {os.path.basename(f): f for f in all_files_after}.values()

    for filename in unique_files_before:
        try:
            with rasterio.open(os.path.join(rename_dir_before, filename)) as src:
                meta = src.meta.copy()
                original_filename = os.path.splitext(filename)[0]
                chop_and_save_tiles(src, meta, 2048, output_folder_pre, original_filename)
        except Exception as e:
            logger.error(f"Failed to process file {filename}: {e}")

    for filename in unique_files_after:
        try:
            with rasterio.open(os.path.join(rename_dir_after, filename)) as src:
                meta = src.meta.copy()
                original_filename = os.path.splitext(filename)[0]
                chop_and_save_tiles(src, meta, 2048, output_folder_after, original_filename)
        except Exception as e:
            logger.error(f"Failed to process file {filename}: {e}")

    logger.info("Processing completed for all files.")

def process_files_predict(folder_path, output_folder_after):
    after_path = os.path.join(folder_path, 'After')

    if not os.path.exists(after_path):
        logger.error("Required 'After' folder is not found.")
        return

    after_jp2_files = [f for f in os.listdir(after_path) if f.endswith(".jp2")]

    prepare_dir_after = './prepare_image/After'
    rename_dir_after = './rename_image/After'
    
    # Create directories if they don't exist
    for directory in [prepare_dir_after, rename_dir_after]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Copy all files to the prepare_image directory
    for filename in after_jp2_files:
        shutil.copy(os.path.join(after_path, filename), os.path.join(prepare_dir_after, filename))

    logger.info("Files copied to prepare_image directory.")

    resample_needed = [("20m", 10), ("60m", 10)]
    resample_pairs = []

    for filename in after_jp2_files:
        if any(res in filename for res, _ in resample_needed):
            resolution = next(new_res for res, new_res in resample_needed if res in filename)
            resampled_filename = rename_file(filename, 'After')
            resample_pairs.append((os.path.join(prepare_dir_after, filename), os.path.join(rename_dir_after, resampled_filename), resolution))

    parallel_resample(resample_pairs)

    # Move and rename non-resampled files to rename_dir
    for filename in after_jp2_files:
        if not any(res in filename for res, _ in resample_needed):
            new_filename = rename_file(filename, 'After')
            shutil.copy(os.path.join(prepare_dir_after, filename), os.path.join(rename_dir_after, new_filename))

    all_files_after = [rename_file(f, 'After') if any(res in f for res, _ in resample_needed) else rename_file(f, 'After') for f in after_jp2_files]

    all_files_after = [os.path.basename(f) for f in all_files_after]

    # Ensure unique filenames
    unique_files_after = {os.path.basename(f): f for f in all_files_after}.values()

    for filename in unique_files_after:
        try:
            with rasterio.open(os.path.join(rename_dir_after, filename)) as src:
                meta = src.meta.copy()
                original_filename = os.path.splitext(filename)[0]
                chop_and_save_tiles(src, meta, 2048, output_folder_after, original_filename)
        except Exception as e:
            logger.error(f"Failed to process file {filename}: {e}")

    logger.info("Processing completed for all files.")

def submit_folder_dnbr(folder_path, output_folder_pre, output_folder_after, config):
    if folder_path and os.path.isdir(folder_path):
        logger.info(f"Processing folder: {folder_path}")
        process_files(folder_path, output_folder_pre, output_folder_after, config)
        logger.info("Processing completed for selected folder.")
        
        # Define the path to the subprocess script
        script_path = "/Users/imdsk/RIDA_Tools/RIDA_Tools/SentinelProcess_Train_dNBR.py"
        
        # Run the script as a subprocess
        try:
            result = subprocess.run(["python", script_path], capture_output=True, text=True, check=True)
            logger.info("Subprocess output:\n" + result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error("Error during subprocess execution:\n" + e.stderr)
    else:
        logger.error("Invalid input or no folder selected")

def submit_folder_rndi(folder_path, output_folder_pre, output_folder_after, config):
    if folder_path and os.path.isdir(folder_path):
        logger.info(f"Processing folder: {folder_path}")
        process_files(folder_path, output_folder_pre, output_folder_after, config)
        logger.info("Processing completed for selected folder.")
        
        # Define the path to the subprocess script
        script_path = "/Users/imdsk/RIDA_Tools/RIDA_Tools/SentinelProcess_Train_rNDI.py"
        
        # Run the script as a subprocess
        try:
            result = subprocess.run(["python", script_path], capture_output=True, text=True, check=True)
            logger.info("Subprocess output:\n" + result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error("Error during subprocess execution:\n" + e.stderr)
    else:
        logger.error("Invalid input or no folder selected")

def submit_folder_predict(folder_path, output_folder_after):
    if folder_path and os.path.isdir(folder_path):
        logger.info(f"Processing folder: {folder_path}")
        process_files_predict(folder_path, output_folder_after)
        logger.info("Processing completed for selected folder.")
        
        # Define the path to the subprocess script
        script_path = "/Users/imdsk/RIDA_Tools/RIDA_Tools/SentinelProcess_Predict.py"
        
        # Run the script as a subprocess
        try:
            result = subprocess.run(["python", script_path], capture_output=True, text=True, check=True)
            logger.info("Subprocess output:\n" + result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error("Error during subprocess execution:\n" + e.stderr)
    else:
        logger.error("Invalid input or no folder selected")
