import rasterio
from rasterio.enums import Resampling

def resample_raster(input_raster, output_raster, new_resolution):
    """
    Resamples a raster dataset to a new resolution.

    Args:
        input_raster (str): Path to the input raster file.
        output_raster (str): Path to the output raster file.
        new_resolution (float): The desired resolution for the output raster.
    """

    with rasterio.open(input_raster) as src:
        transform = src.transform
        data = src.read(
            out_shape=(
                src.count,
                int(src.height * src.transform.a / new_resolution),
                int(src.width * src.transform.a / new_resolution)
            ),  
            resampling=Resampling.nearest  # You can adjust the resampling method here
        )
        profile = src.profile
        profile.update(transform=transform, width=data.shape[2], height=data.shape[1])

        with rasterio.open(output_raster, 'w', **profile) as dst:
            dst.write(data)

# Example usage with basic input/output paths
if __name__ == "__main__":
    input_raster_path = "path/to/your/input.tif"
    output_raster_path = "path/to/output.tif"
    new_resolution = 5  # Example new resolution in meters (adjust as needed)

    resample_raster(input_raster_path, output_raster_path, new_resolution)
