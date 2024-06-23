import os
import shutil
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from shapely.geometry import Polygon, mapping
import fiona
from pyproj import Transformer
from fiona.crs import from_epsg
import rasterio
from rasterio.enums import Resampling
from rasterio.mask import mask
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Define the directory paths
Drive = "D:\RIDA-Docker\work\sentinel_process"
Image_Finish = os.path.join(Drive, "Image_Finish")
Image_Missing = os.path.join(Drive, "Image_Missing")
Output = os.path.join(Drive, "Output")
Rtbcon = os.path.join(Drive, "Raster_BurnCon")
Rtbreg = os.path.join(Drive, "Raster_BurnReg")
RtbShape = os.path.join(Drive, "Raster_BurnShape")
RtbLevel = os.path.join(Drive, "Raster_BurnLevel")
Image_Pre = os.path.join(Drive, "Image_Pre")
Image = os.path.join(Drive, "Image")

# SHP Creation
def execute_script(csv_filename, base_path):
    df = pd.read_csv(csv_filename)
    # transformer = Transformer.from_crs("epsg:4326", "epsg:32647", always_xy=True)
    transformer = Transformer.from_crs("epsg:4326", "epsg:32648", always_xy=True)
    schema = {
        'geometry': 'Polygon',
        'properties': {'id': 'int', 'area': 'str'}
    }
    shp_directory = os.path.join(base_path, 'SHP')
    os.makedirs(shp_directory, exist_ok=True)
    
    for index, row in df.iterrows():
        try:
            top_left_x, top_left_y = transformer.transform(row['top_left_lon'], row['top_left_lat'])
            bottom_right_x, bottom_right_y = transformer.transform(row['bottom_right_lon'], row['bottom_right_lat'])
            geometry = Polygon([
                (top_left_x, top_left_y),
                (bottom_right_x, top_left_y),
                (bottom_right_x, bottom_right_y),
                (top_left_x, bottom_right_y)
            ])
            area = row['area']
            area_directory = os.path.join(shp_directory, area)
            os.makedirs(area_directory, exist_ok=True)
            shapefile_name = os.path.join(area_directory, f'{area}.shp')
            with fiona.open(shapefile_name, 'w', driver='ESRI Shapefile', crs=from_epsg(32647), schema=schema) as out_file:
                out_file.write({
                    'geometry': mapping(geometry),
                    'properties': {'id': index, 'area': area}
                })
            print(f"Shapefile {shapefile_name} created successfully in the '{area}' folder within 'SHP'.")
        except Exception as e:
            print(f"Failed to create shapefile for {area}: {e}")

# File Checker
REQUIRED_FILES_BEFORE = [
    "B02_10m.jp2", "B03_10m.jp2", "B04_10m.jp2", "B08_10m.jp2"
]
REQUIRED_FILES_AFTER = [
    "B02_10m.jp2", "B03_10m.jp2", "B04_10m.jp2", "B08_10m.jp2",
    "B05_20m.jp2", "B06_20m.jp2", "B07_20m.jp2", "B8A_20m.jp2",
    "B09_60m.jp2", "B12_20m.jp2"
]

def check_files_in_directory(directory, required_files):
    existing_files = os.listdir(directory)
    missing_files = [file for file in required_files if not any(f.endswith(file) for f in existing_files)]
    return missing_files, existing_files

def process_files(selected_folder, config=None):
    before_path = os.path.join(selected_folder, 'Before')
    after_path = os.path.join(selected_folder, 'After')
    missing_before, existing_before = check_files_in_directory(before_path, REQUIRED_FILES_BEFORE)
    missing_after, existing_after = check_files_in_directory(after_path, REQUIRED_FILES_AFTER)
    if missing_before or missing_after:
        response = "Missing files detected:"
        if missing_before:
            response += f"\n'Before' folder missing: {', '.join(missing_before)}"
        if missing_after:
            response += f"\n'After' folder missing: {', '.join(missing_after)}"
    else:
        response = "All required files are present in both 'Before' and 'After' folders."
    return response, existing_before, existing_after



# Folder Mover
def move_folders(base_path):
    image_pre_path = os.path.join(base_path, Image_Pre)
    image_path = os.path.join(base_path, Image)
    if not os.path.exists(image_pre_path):
        os.makedirs(image_pre_path)
    if not os.path.exists(image_path):
        os.makedirs(image_path)

    before_cropped_path = os.path.join(base_path, "Resampled_Before")
    after_cropped_path = os.path.join(base_path, "Resampled_After")

    # Move folders from Before_Cropped to Image_Pre
    for folder in os.listdir(before_cropped_path):
        source_folder = os.path.join(before_cropped_path, folder)
        destination_folder = os.path.join(image_pre_path, folder)
        if os.path.isdir(source_folder):
            shutil.move(source_folder, destination_folder)
            print(f"Moved {source_folder} to {destination_folder}")

    # Move folders from After_Cropped to Image
    for folder in os.listdir(after_cropped_path):
        source_folder = os.path.join(after_cropped_path, folder)
        destination_folder = os.path.join(image_path, folder)
        if os.path.isdir(source_folder):
            shutil.move(source_folder, destination_folder)
            print(f"Moved {source_folder} to {destination_folder}")

# Crop Process
def crop_and_show_images(base_path, shp_directory, image_folder, result_folder):
    result_base_path = os.path.join(base_path, result_folder)
    if not os.path.exists(result_base_path):
        os.makedirs(result_base_path)

    print(f"Checking shapefiles in directory: {shp_directory}")
    print(f"Contents: {os.listdir(shp_directory)}")

    for area_folder in os.listdir(shp_directory):
        area_path = os.path.join(shp_directory, area_folder)
        if not os.path.isdir(area_path):
            continue

        print(f"Checking area folder: {area_path}")
        print(f"Contents: {os.listdir(area_path)}")

        for shp_file in os.listdir(area_path):
            if not shp_file.endswith('.shp'):
                continue

            shp_path = os.path.join(area_path, shp_file)
            area_name = os.path.basename(shp_path).replace('.shp', '')
            area_result_path = os.path.join(result_base_path, area_name)
            if not os.path.exists(area_result_path):
                os.makedirs(area_result_path)

            print(f"Processing shapefile: {shp_path}")

            with fiona.open(shp_path, "r") as shapefile:
                aoiGeom = [feature["geometry"] for feature in shapefile]

            bandPath = image_folder  # Use the full path directly
            bandNames = [name for name in os.listdir(bandPath) if name.endswith('.jp2')]

            if not bandNames:
                print(f"No files found in {bandPath}.")
                continue

            print(f"Found {len(bandNames)} .jp2 files in {bandPath}")

            fig, ax = plt.subplots(figsize=(4, 4), dpi=72)
            any_cropped = False

            for bandName in bandNames:
                rasterPath = os.path.join(bandPath, bandName)
                with rasterio.open(rasterPath) as src:
                    out_image, out_transform = mask(src, aoiGeom, crop=True)
                    out_meta = src.meta.copy()
                    out_meta.update({"driver": "JP2OpenJPEG", "height": out_image.shape[1], "width": out_image.shape[2], "transform": out_transform})

                    original_name = bandName
                    parts = original_name.split('_')
                    new_name = bandName  # Initialize new_name with the original bandName

                    if result_folder == 'Before_Cropped':
                        if '20m' in original_name or '60m' in original_name:
                            if 'B12' in original_name:
                                new_name = f"{parts[0]}_B1210.jp2"
                            else:
                                parts[-2] = parts[-2].replace('20m', '10').replace('60m', '10')
                                new_name = f"{parts[0]}_{parts[2]}10.jp2"
                        else:
                            new_name = f"{parts[0]}_{parts[2]}.jp2"

                    elif result_folder == 'After_Cropped':
                        if '20m' in original_name or '60m' in original_name:
                            if 'B12' in original_name:
                                new_name = f"{original_name[:22]}_B1210.jp2"
                            else:
                                parts[-2] = parts[-2].replace('20m', '10').replace('60m', '10')
                                new_name = f"{parts[0]}_{parts[1]}_{parts[2]}10.jp2"
                        else:
                            new_name = f"{parts[0]}_{parts[1]}_{parts[2]}.jp2"

                    cropped_image_path = os.path.join(area_result_path, new_name)
                    with rasterio.open(cropped_image_path, "w", **out_meta) as dest:
                        dest.write(out_image)
                    print(f"Cropped image saved to: {cropped_image_path}")
                    any_cropped = True

                    if np.random.rand() < 1 / len(bandNames):
                        chosen_raster = rasterio.open(cropped_image_path)
                        show(chosen_raster, cmap='Blues', ax=ax)
                        ax.set_title(f"Area: {area_name}")
                        plt.show()

            if any_cropped:
                print(f"Cropped images saved for {shp_file} in the '{area_name}' folder within '{result_folder}'.")
            else:
                print(f"Warning: No images were cropped for {shp_file} in '{result_folder}'.")

# Resampling and processing functions
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
            profile.update(transform=transform, height=data.shape[1], width=data.shape[2])
            with rasterio.open(output_raster, 'w', **profile) as dst:
                dst.write(data)
        logger.info(f"Resampled raster saved to {output_raster}")
    except Exception as e:
        logger.error(f"Failed to resample raster {input_raster}: {e}")


def get_all_files_with_extension(folder, extension):
    files = []
    for root, _, filenames in os.walk(folder):
        for filename in filenames:
            if filename.endswith(extension):
                files.append(os.path.join(root, filename))
    return files

def parallel_resample_test(input_folder, output_folder, new_resolution):
    input_rasters = get_all_files_with_extension(input_folder, ".jp2")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for input_raster in input_rasters:
            relative_path = os.path.relpath(input_raster, input_folder)
            output_raster = os.path.join(output_folder, relative_path)
            os.makedirs(os.path.dirname(output_raster), exist_ok=True)
            futures.append(
                executor.submit(
                    resample_raster,
                    input_raster,
                    output_raster,
                    new_resolution
                )
            )
        for future in futures:
            future.result()


def aoi_submit_folder_rndi_test(selected_folder, config):
    output_messages = []

    # Step 1: SHP Creation
    csv_file = os.path.join(selected_folder, "Coordinate.csv")
    execute_script(csv_file, selected_folder)
    output_messages.append("SHP files created.")

    # Step 2: File Checker
    response, existing_before, existing_after = process_files(selected_folder, config)
    output_messages.append(f"Data processed for folder: {selected_folder}")
    output_messages.append(response)

    # Step 3: Cropping
    before_folder_test = os.path.join(selected_folder, "Before")
    after_folder_test = os.path.join(selected_folder, "After")
    shp_path = os.path.join(selected_folder, "SHP")
    if existing_before:
        crop_and_show_images(selected_folder, shp_path, before_folder_test, 'Before_Cropped')
        output_messages.append("Before images cropped and shown.")
    if existing_after:
        crop_and_show_images(selected_folder, shp_path, after_folder_test, 'After_Cropped')
        output_messages.append("After images cropped and shown.")

    # Step 4: Resampling
    before_folder = os.path.join(selected_folder, "Before_Cropped")
    after_folder = os.path.join(selected_folder, "After_Cropped")
    resampled_before_folder = os.path.join(selected_folder, "Resampled_Before")
    resampled_after_folder = os.path.join(selected_folder, "Resampled_After")
    parallel_resample_test(before_folder, resampled_before_folder, new_resolution=10)
    parallel_resample_test(after_folder, resampled_after_folder, new_resolution=10)
    output_messages.append("Resampling completed.")

    # Step 5: Move Folders
    try:
        move_folders(selected_folder)
        output_messages.append("Folders moved.")
    except Exception as e:
        logger.error(f"Error moving folders: {e}")
        output_messages.append(f"Error moving folders: {e}")

    # Step 6: Execute SentinelProcess script
    try:
        script_path = r"D:\RIDA-Docker\work\data_preparation\SentinelProcess_Train_rNDI.py"
        subprocess.run(["python", script_path])
        output_messages.append("SentinelProcess script executed.")
    except Exception as e:
        logger.error(f"Error executing SentinelProcess script: {e}")
        output_messages.append(f"Error executing SentinelProcess script: {e}")

    logger.info("Training AOI process completed.")
    output_messages.append("Training AOI process completed.")

    return "\n".join(output_messages)


def aoi_submit_folder_dnbr_test(selected_folder, config):
    output_messages = []

    # Step 1: SHP Creation
    csv_file = os.path.join(selected_folder, "Coordinate.csv")
    execute_script(csv_file, selected_folder)
    output_messages.append("SHP files created.")

    # Step 2: File Checker
    response, existing_before, existing_after = process_files(selected_folder, config)
    output_messages.append(f"Data processed for folder: {selected_folder}")
    output_messages.append(response)

    # Step 3: Cropping
    before_folder_test = os.path.join(selected_folder, "Before")
    after_folder_test = os.path.join(selected_folder, "After")
    shp_path = os.path.join(selected_folder, "SHP")
    if existing_before:
        crop_and_show_images(selected_folder, shp_path, before_folder_test, 'Before_Cropped')
        output_messages.append("Before images cropped and shown.")
    if existing_after:
        crop_and_show_images(selected_folder, shp_path, after_folder_test, 'After_Cropped')
        output_messages.append("After images cropped and shown.")

    # Step 4: Resampling
    before_folder = os.path.join(selected_folder, "Before_Cropped")
    after_folder = os.path.join(selected_folder, "After_Cropped")
    resampled_before_folder = os.path.join(selected_folder, "Resampled_Before")
    resampled_after_folder = os.path.join(selected_folder, "Resampled_After")
    parallel_resample_test(before_folder, resampled_before_folder, new_resolution=10)
    parallel_resample_test(after_folder, resampled_after_folder, new_resolution=10)
    output_messages.append("Resampling completed.")

    # Step 5: Move Folders
    try:
        move_folders(selected_folder)
        output_messages.append("Folders moved.")
    except Exception as e:
        logger.error(f"Error moving folders: {e}")
        output_messages.append(f"Error moving folders: {e}")

    # Step 6: Execute SentinelProcess script
    try:
        script_path = r"D:\RIDA-Docker\work\data_preparation\SentinelProcess_Train_dNBR.py"
        subprocess.run(["python", script_path])
        output_messages.append("SentinelProcess script executed.")
    except Exception as e:
        logger.error(f"Error executing SentinelProcess script: {e}")
        output_messages.append(f"Error executing SentinelProcess script: {e}")

    logger.info("Training AOI process completed.")
    output_messages.append("Training AOI process completed.")

    return "\n".join(output_messages)



def aoi_submit_folder_predict_test(selected_folder):
    output_messages = []

    # Step 1: SHP Creation
    csv_file = os.path.join(selected_folder, "Coordinate.csv")
    execute_script(csv_file, selected_folder)
    output_messages.append("SHP files created.")

    # Step 2: File Checker
    response, existing_before, existing_after = process_files(selected_folder)
    output_messages.append(f"Data processed for folder: {selected_folder}")
    output_messages.append(response)

    # Step 3: Cropping
    before_folder_test = os.path.join(selected_folder, "Before")
    after_folder_test = os.path.join(selected_folder, "After")
    shp_path = os.path.join(selected_folder, "SHP")
    if existing_before:
        crop_and_show_images(selected_folder, shp_path, before_folder_test, 'Before_Cropped')
        output_messages.append("Before images cropped and shown.")
    if existing_after:
        crop_and_show_images(selected_folder, shp_path, after_folder_test, 'After_Cropped')
        output_messages.append("After images cropped and shown.")

    # Step 4: Resampling
    before_folder = os.path.join(selected_folder, "Before_Cropped")
    after_folder = os.path.join(selected_folder, "After_Cropped")
    resampled_before_folder = os.path.join(selected_folder, "Resampled_Before")
    resampled_after_folder = os.path.join(selected_folder, "Resampled_After")
    parallel_resample_test(before_folder, resampled_before_folder, new_resolution=10)
    parallel_resample_test(after_folder, resampled_after_folder, new_resolution=10)
    output_messages.append("Resampling completed.")

    # Step 5: Move Folders
    try:
        move_folders(selected_folder)
        output_messages.append("Folders moved.")
    except Exception as e:
        logger.error(f"Error moving folders: {e}")
        output_messages.append(f"Error moving folders: {e}")

    # Step 6: Execute SentinelProcess script
    try:
        script_path = r"D:\RIDA-Docker\work\data_preparation\SentinelProcess_Predict.py"
        subprocess.run(["python", script_path])
        output_messages.append("SentinelProcess script executed.")
    except Exception as e:
        logger.error(f"Error executing SentinelProcess script: {e}")
        output_messages.append(f"Error executing SentinelProcess script: {e}")

    logger.info("Training AOI process completed.")
    output_messages.append("Training AOI process completed.")

    return "\n".join(output_messages)


