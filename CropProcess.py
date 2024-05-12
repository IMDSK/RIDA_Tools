import os
import fiona
import rasterio
from rasterio.mask import mask
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np

def crop_and_show_images(base_path, shp_directory, image_folder, result_folder):
    rstPath = os.path.join(base_path, result_folder)
    if not os.path.exists(rstPath):
        os.makedirs(rstPath)

    for shp_file in os.listdir(shp_directory):
        if shp_file.endswith('.shp'):
            shp_path = os.path.join(shp_directory, shp_file)
            with fiona.open(shp_path, "r") as shapefile:
                aoiGeom = [feature["geometry"] for feature in shapefile]
                bandPath = os.path.join(base_path, image_folder)
                bandNames = [name for name in os.listdir(bandPath) if name.endswith('.jp2')]

                # Randomly pick one image to plot from the set
                chosen_image_name = np.random.choice(bandNames)
                chosen_raster_path = os.path.join(bandPath, chosen_image_name)
                chosen_raster = rasterio.open(chosen_raster_path)
                fig, ax = plt.subplots(figsize=(4, 4),dpi= 72)
                show(chosen_raster, cmap='Blues', ax=ax)

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

                        cropped_image_name = f"{shp_file.replace('.shp', '')}_{bandName}"
                        cropped_image_path = os.path.join(rstPath, cropped_image_name)
                        with rasterio.open(cropped_image_path, "w", **out_meta) as dest:
                            dest.write(out_image)

                        # Plot the cropped image on top of the original image
                        with rasterio.open(cropped_image_path) as cropped_image:
                            show(cropped_image, cmap='viridis', ax=ax, alpha=0.5)

                ax.set_ylim(chosen_raster.bounds.bottom, chosen_raster.bounds.top)
                ax.set_xlim(chosen_raster.bounds.left, chosen_raster.bounds.right)
                plt.show()

                print(f"Cropped images saved for {shp_file} in the '{image_folder}' folder.")