import os
import fiona
import rasterio
from rasterio.mask import mask
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np

def crop_and_show_images(base_path, shp_directory, image_folder, result_folder):
    result_base_path = os.path.join(base_path, result_folder)
    if not os.path.exists(result_base_path):
        os.makedirs(result_base_path)

    for shp_file in os.listdir(shp_directory):
        if shp_file.endswith('.shp'):
            shp_path = os.path.join(shp_directory, shp_file)
            area_name = os.path.basename(shp_path).replace('.shp', '')
            area_result_path = os.path.join(result_base_path, area_name)
            if not os.path.exists(area_result_path):
                os.makedirs(area_result_path)

            with fiona.open(shp_path, "r") as shapefile:
                aoiGeom = [feature["geometry"] for feature in shapefile]
                bandPath = os.path.join(base_path, image_folder)
                bandNames = [name for name in os.listdir(bandPath) if name.endswith('.jp2')]

                fig, ax = plt.subplots(figsize=(4, 4), dpi=72)

                for bandName in bandNames:
                    rasterPath = os.path.join(bandPath, bandName)
                    with rasterio.open(rasterPath) as src:
                        out_image, out_transform = mask(src, aoiGeom, crop=True)
                        out_meta = src.meta.copy()
                        out_meta.update({
                            "driver": "JP2OpenJPEG",
                            "height": out_image.shape[1],
                            "width": out_image.shape[2],
                            "transform": out_transform
                        })

                        cropped_image_path = os.path.join(area_result_path, bandName)
                        with rasterio.open(cropped_image_path, "w", **out_meta) as dest:
                            dest.write(out_image)
                            print(f"Cropped image saved to: {cropped_image_path}")

                        # Randomly select one image to plot
                        if np.random.rand() < 1 / len(bandNames):
                            chosen_raster = rasterio.open(cropped_image_path)
                            show(chosen_raster, cmap='Blues', ax=ax)

                ax.set_title(f"Area: {area_name}")
                plt.show()

                print(f"Cropped images saved for {shp_file} in the '{area_name}' folder within '{result_folder}'.")
