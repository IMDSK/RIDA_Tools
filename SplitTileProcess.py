import os
import fiona
import rasterio
from rasterio.mask import mask
from rasterio.plot import show
import matplotlib.pyplot as plt
import warnings
from rasterio.windows import Window
from shapely.geometry import box

def crop_and_chop_images(base_path, shp_path, image_folder, result_folder, tile_size=1):
    # Ensure the result directory exists
    rstPath = os.path.join(base_path, result_folder)
    if not os.path.exists(rstPath):
        os.makedirs(rstPath)

    try:
        with fiona.open(shp_path, "r") as aoiFile:
            aoiGeom = [feature["geometry"] for feature in aoiFile]
            print(f"CRS for shapefile: {aoiFile.crs}")
            print(f"Bounds for shapefile: {aoiFile.bounds}")

            bandPath = os.path.join(base_path, image_folder)
            bandNames = [name for name in os.listdir(bandPath) if name.endswith('.jp2')]

            for bandName in bandNames:
                rasterPath = os.path.join(bandPath, bandName)
                try:
                    with rasterio.open(rasterPath) as rasterBand:
                        print(f"CRS for raster {bandName}: {rasterBand.crs}")
                        print(f"Bounds for raster {bandName}: {rasterBand.bounds}")

                        try:
                            # Suppress the "Image data of dtype object cannot be converted to float" error
                            with warnings.catch_warnings():
                                warnings.filterwarnings("ignore", message="Image data of dtype object cannot be converted to float")
                                outImage, outTransform = mask(rasterBand, aoiGeom, crop=True)

                            if outImage.any():
                                outMeta = rasterBand.meta.copy()
                                outMeta.update({
                                    "driver": 'JP2OpenJPEG',
                                    "height": outImage.shape[1],
                                    "width": outImage.shape[2],
                                    "transform": outTransform
                                })

                                # Save the cropped image
                                outRasterPath = os.path.join(rstPath, bandName)
                                with rasterio.open(outRasterPath, "w", **outMeta) as outRaster:
                                    outRaster.write(outImage)

                                # Chop the cropped area into smaller tiles
                                chop_and_save_tiles(outRaster, outMeta, tile_size, rstPath, bandName)

                            else:
                                print(f"No data to process for {bandName} with the shapefile.")

                            print(f"Processed {bandName} using the shapefile.")

                        except ValueError as e:
                            # Log a warning for developers about the potential issue
                            print(f"Warning: Encountered data type issue while processing {bandName} with the shapefile: {e}")

                except Exception as e:
                    print(f"Failed to process {bandName} with the shapefile: {e}")

    except Exception as e:
        print(f"Error opening shapefile: {e}")

    print("Cropped and chopped images saved.")

def chop_and_save_tiles(cropped_raster, meta, tile_size, output_folder, bandName):
    # Get the bounds of the cropped raster
    bounds = cropped_raster.bounds
    left, bottom, right, top = bounds

    # Calculate the number of tiles
    tile_width = meta['width'] // tile_size
    tile_height = meta['height'] // tile_size

    # Create tiles
    for row in range(tile_height):
        for col in range(tile_width):
            # Calculate the window for the tile
            window = Window(col * tile_size, row * tile_size, tile_size, tile_size)
            tile_data = cropped_raster.read(window=window)

            if tile_data.any():
                # Calculate the bounds of the tile
                x_min = left + col * tile_size * meta['transform'][0]
                y_min = bottom + row * tile_size * meta['transform'][4]
                x_max = x_min + tile_size * meta['transform'][0]
                y_max = y_min + tile_size * meta['transform'][4]
                tile_bounds = box(x_min, y_min, x_max, y_max)

                # Save the tile
                tile_name = f"{bandName}_{row}_{col}.jp2"
                tile_path = os.path.join(output_folder, tile_name)
                meta.update({
                    "height": tile_size,
                    "width": tile_size,
                    "transform": rasterio.transform.from_bounds(*tile_bounds.bounds, tile_size, tile_size)
                })

                with rasterio.open(tile_path, "w", **meta) as tile_raster:
                    tile_raster.write(tile_data)

                print(f"Saved tile {tile_name}")

crop_and_chop_images(base_path, shp_path, 'image_folder', 'result_folder', tile_size=10)