import ipywidgets as widgets
from ipywidgets import VBox, Label, Button, Dropdown, Accordion, Tab
from ipyfilechooser import FileChooser
from IPython.display import display, clear_output, Image
import logging
import json
import os
import shutil
import rasterio
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd

# Importing the functions from the image_processing.py module
from image_processing import submit_folder_dnbr, submit_folder_rndi, submit_folder_predict
from image_processing_aoi import aoi_submit_folder_rndi_test,aoi_submit_folder_dnbr_test,aoi_submit_folder_predict_test

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

style = {'description_width': '150px'}
layout = {'width' : '400px'}

# Load the configuration values dNBR
config_path_dnbr = "./config_dnbr.json"
with open(config_path_dnbr, "r") as f:
    default_config_dnbr = json.load(f)

# Create widgets for configuration values with default values
burn_con_lv1_threshold_dnbr = widgets.FloatSlider(
    value=default_config_dnbr["burn_con_lv1_threshold_dnbr"],
    min=0,
    max=1,
    step=0.01,
    description='dNBR:',
    style = style,
    layout = layout
)
burn_con_lv3_threshold_dnbr = widgets.FloatSlider(
    value=default_config_dnbr["burn_con_lv3_threshold_dnbr"],
    min=0,
    max=1,
    step=0.01,
    description='NDVI:',
    style = style,
    layout = layout
)
burn_con_lv4_threshold_dnbr = widgets.IntText(
    value=default_config_dnbr["burn_con_lv4_threshold_dnbr"],
    description='Wave reflection value:',
    style = style,
    layout = layout
)

# Load the configuration values rNDI
config_path_rndi = "./config_rndi.json"
with open(config_path_rndi, "r") as f:
    default_config_rndi = json.load(f)

# Create widgets for configuration values with default values
burn_con_lv1_threshold_rndi = widgets.FloatSlider(
    value=default_config_rndi["burn_con_lv1_threshold_rndi"],
    min=0,
    max=1,
    step=0.01,
    description='rNDI:',
    style = style,
    layout = layout
)
burn_con_lv3_threshold_rndi = widgets.FloatSlider(
    value=default_config_rndi["burn_con_lv3_threshold_rndi"],
    min=0,
    max=1,
    step=0.01,
    description='NDVI:',
    style = style,
    layout = layout
)
burn_con_lv4_threshold_rndi = widgets.IntText(
    value=default_config_rndi["burn_con_lv4_threshold_rndi"],
    description='Wave reflection value:',
    style = style,
    layout = layout
)

# Folder chooser and process button
fc = FileChooser("resource")
submit_button = Button(description="Submit")
folder_label = Label("")

# Input widgets for output folders
output_folder_input_pre = widgets.Text(
    value='sentinel_process\Image_pre',
    description='Output Folder Pre:',
)
output_folder_input_after = widgets.Text(
    value='sentinel_process\Image',
    description='Output Folder After:',
)

# Adjust and Save Result buttons
adjust_button = Button(description="Adjust")
save_button = Button(description="Save Result")

# Output widget to display image and buttons
output_widget = widgets.Output()

def plot_burn_con_image(pipeline_type='Train'):
    try:
        if pipeline_type == 'Predict':
            print("No image plotting required for the Predict pipeline.")
            return None

        burn_con_dir = r'sentinel_process\Raster_BurnCon'
        shp_dir = r'sentinel_process\Raster_BurnShape'
        area_dirs = [d for d in os.listdir(burn_con_dir) if os.path.isdir(os.path.join(burn_con_dir, d))]

        if not area_dirs:
            print("No area directories found in the BurnCon directory.")
            return None

        for area_dir in area_dirs:
            area_path = os.path.join(burn_con_dir, area_dir)
            tif_files = [f for f in os.listdir(area_path) if f.endswith('.tif')]

            if tif_files:
                burn_con_image_path = os.path.join(area_path, tif_files[0])
                shp_path = next((os.path.join(shp_dir, area_dir, f) for f in os.listdir(os.path.join(shp_dir, area_dir)) if f.endswith('.shp')), None)
                if shp_path is None:
                    print(f"No .shp file found in the {area_dir} directory.")
                    continue

                with rasterio.open(burn_con_image_path) as src:
                    band2 = src.read(1)
                    band3 = src.read(2)
                    band4 = src.read(3)
                    profile = src.profile

                true_color_image = np.dstack((band4, band3, band2))
                true_color_normalized = true_color_image / true_color_image.max()

                gdf = gdf.apply(lambda row: row.geometry.hpr_flip(), axis=1)
                
                # Create side by side plots
                fig, axes = plt.subplots(1, 2, figsize=(16, 8), dpi=100)

                # Plot true color image
                axes[0].imshow(true_color_normalized)
                axes[0].set_title(f'True Color Image: {area_dir}')
                axes[0].axis('off')

                # Read the shapefile if found
                if shp_path is not None:
                    shp_geodf = gpd.read_file(shp_path)
                    shp_geodf.plot(ax=axes[1], color='red', edgecolor='red', alpha=0.5)

                    # Flip the y-axis for the shapefile plot
                    axes[1].set_ylim([axes[1].get_ylim()[1], axes[1].get_ylim()[0]])  # Invert y-axis limits
                    axes[1].set_title(f'Shapefile Only: {area_dir}')
                    axes[1].axis('off')

                plt.tight_layout()
                plt.show()  # Display the plot for each area
            else:
                print(f"No .tif files found in the {area_dir} directory.")

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def on_submit_clicked(b):
    folder_path = fc.selected_path
    selected_folder = fc.selected_path
    output_folder_pre = output_folder_input_pre.value
    output_folder_after = output_folder_input_after.value
    
    # Create a temporary config dictionary with adjusted values : dNBR
    temp_config_dnbr = default_config_dnbr.copy()
    temp_config_dnbr["burn_con_lv1_threshold_dnbr"] = burn_con_lv1_threshold_dnbr.value
    temp_config_dnbr["burn_con_lv3_threshold_dnbr"] = burn_con_lv3_threshold_dnbr.value
    temp_config_dnbr["burn_con_lv4_threshold_dnbr"] = burn_con_lv4_threshold_dnbr.value

    # Create a temporary config dictionary with adjusted values : rNDI
    temp_config_rndi = default_config_rndi.copy()
    temp_config_rndi["burn_con_lv1_threshold_rndi"] = burn_con_lv1_threshold_rndi.value
    temp_config_rndi["burn_con_lv3_threshold_rndi"] = burn_con_lv3_threshold_rndi.value
    temp_config_rndi["burn_con_lv4_threshold_rndi"] = burn_con_lv4_threshold_rndi.value

    if section_tabs.selected_index == 0:  # Fully Tile
        if fully_tile_accordion.selected_index == 0:
            submit_folder_dnbr(folder_path, output_folder_pre, output_folder_after, temp_config_dnbr)
        elif fully_tile_accordion.selected_index == 1:
            submit_folder_rndi(folder_path, output_folder_pre, output_folder_after, temp_config_rndi)
        elif fully_tile_accordion.selected_index == 2:
            submit_folder_predict(folder_path,output_folder_after)
            
    if section_tabs_aoi.selected_index == 0:  # AOI
        if aoi_accordion.selected_index == 0:
            aoi_submit_folder_dnbr_test(selected_folder, temp_config_dnbr)
        elif aoi_accordion.selected_index == 1:
            aoi_submit_folder_rndi_test(selected_folder, temp_config_rndi)
        elif aoi_accordion.selected_index == 2:
            aoi_submit_folder_predict_test(selected_folder)

        folder_label.value = "Processing completed"

        # Show result and buttons after processing
        with output_widget:
            clear_output()
            burn_con_fig = plot_burn_con_image()
            if burn_con_fig is not None:
                display(burn_con_fig)
            display(adjust_button, save_button)


def on_adjust_clicked(b):
    # Clear all processed files and prompt to select Resource folder again
    try:
        shutil.rmtree('prepare_image')
    except FileNotFoundError:
        pass  # Skip if the directory does not exist

    try:
        shutil.rmtree('rename_image')
    except FileNotFoundError:
        pass

    try:
        shutil.rmtree(r'resource\T47QNB\2023\SHP')
    except FileNotFoundError:
        pass  # Skip if the directory does not exist

    try:
        shutil.rmtree(r'resource\T47QNB\2023\Before_Cropped')
    except FileNotFoundError:
        pass  # Skip if the directory does not exist

    try:
        shutil.rmtree(r'resource\T47QNB\2023\After_Cropped')
    except FileNotFoundError:
        pass

    try:
        shutil.rmtree(r'resource\T47QNB\2023\Resampled_After')
    except FileNotFoundError:
        pass

    try:
        shutil.rmtree(r'resource\T47QNB\2023\Resampled_Before')
    except FileNotFoundError:
        pass



    shutil.rmtree(r'sentinel_process')
    os.makedirs(r'sentinel_process')
    os.makedirs(r'sentinel_process\Image')
    os.makedirs(r'sentinel_process\Image_Finish')
    os.makedirs(r'sentinel_process\Image_Missing')
    os.makedirs(r'sentinel_process\Image_pre')
    os.makedirs(r'sentinel_process\Output')
    os.makedirs(r'sentinel_process\Raster_BurnCon')
    os.makedirs(r'sentinel_process\Raster_BurnShape')
    os.makedirs(r'sentinel_process\Raster_BurnLevel')
    
    with output_widget:
        clear_output()
    display(section_tabs)



def on_save_clicked(b):
    src_folder = 'sentinel_process\Raster_BurnCon'
    dest_base_folder = 'dataframe'

    if not os.path.exists(dest_base_folder):
        os.makedirs(dest_base_folder)

    for area_dir in os.listdir(src_folder):
        area_path = os.path.join(src_folder, area_dir)
        if os.path.isdir(area_path):
            folder_counter = 0  # Initialize a counter for folders
            for file_name in os.listdir(area_path):
                if file_name.endswith('.tif'):
                    parts = file_name.split('_')
                    tile_name = parts[0]
                    date = parts[1][:8]  # Use full date (YYYYMMDD)
                    year = date[:4]
                    month = date[4:6]

                    if fully_tile_accordion.selected_index == 2 or aoi_accordion.selected_index == 2:
                        pipeline_type = "Predict"
                    else:
                        pipeline_type = "Train"

                    # Create a unique folder name by appending a counter
                    dest_folder_base = os.path.join(dest_base_folder, pipeline_type, tile_name, year, month, f"{tile_name}_{date}")
                    dest_folder = dest_folder_base

                    while os.path.exists(dest_folder):
                        folder_counter += 1
                        dest_folder = f"{dest_folder_base}_{folder_counter}"

                    if not os.path.exists(dest_folder):
                        os.makedirs(dest_folder)
                        print(f"Created directory: {dest_folder}")  # Log the created directory

                    # Copy all files from the area directory
                    for area_file in os.listdir(area_path):
                        src_file = os.path.join(area_path, area_file)
                        dest_file = os.path.join(dest_folder, area_file)  # Keep the original file name
                        shutil.copy2(src_file, dest_file)  # Use copy2 to preserve metadata
                        print(f"Moved {src_file} to {dest_file}")  # Log the source and destination paths
                    break  # Only need one .tif file to determine the structure

    # Now that all files are copied, you can safely clean up
    try:
        shutil.rmtree('prepare_image')
        print(f"Removed directory: prepare_image")
    except FileNotFoundError:
        pass  # Skip if the directory does not exist

    try:
        shutil.rmtree('rename_image')
        print(f"Removed directory: rename_image")
    except FileNotFoundError:
        pass

    try:
        shutil.rmtree(r'resource\T47QNB\2023\SHP')
        print(f"Removed directory: resource\T47QNB\2023\SHP")
    except FileNotFoundError:
        pass  # Skip if the directory does not exist

    try:
        shutil.rmtree(r'T47QNB\2023\Before_Cropped')
        print(f"Removed directory: resource\T47QNB\2023\Before_Cropped")
    except FileNotFoundError:
        pass  # Skip if the directory does not exist

    try:
        shutil.rmtree(r'T47QNB\2023\After_Cropped')
        print(f"Removed directory: resource\T47QNB\2023\After_Cropped")
    except FileNotFoundError:
        pass

    try:
        shutil.rmtree(r'T47QNB\2023\Resampled_After')
        print(f"Removed directory: resource\T47QNB\2023\Resampled_After")
    except FileNotFoundError:
        pass

    try:
        shutil.rmtree(r'T47QNB\2023\Resampled_Before')
        print(f"Removed directory: resource\T47QNB\2023\Resampled_Before")
    except FileNotFoundError:
        pass

    shutil.rmtree(r'sentinel_process')
    os.makedirs(r'sentinel_process')
    os.makedirs(r'sentinel_process\Image')
    print(f"Created directory: sentinel_process\Image")
    os.makedirs(r'sentinel_process\Image_Finish')
    print(f"Created directory:sentinel_process\Image_Finish")
    os.makedirs(r'sentinel_process\Image_Missing')
    print(f"Created directory: sentinel_process\Image_Missing")
    os.makedirs(r'sentinel_process\Image_pre')
    print(f"Created directory: sentinel_process\Image_pre")
    os.makedirs(r'sentinel_process\Output')
    print(f"Created directory: sentinel_process\Output")
    os.makedirs(r'sentinel_process\Raster_BurnCon')
    print(f"Created directory: sentinel_process\Raster_BurnCon")
    os.makedirs(r'sentinel_process\Raster_BurnShape')
    print(f"Created directory: sentinel_process\Raster_BurnShape")
    os.makedirs(r'sentinel_process\Raster_BurnLevel')
    print(f"Created directory: sentinel_process\Raster_BurnLevel")

    with output_widget:
        clear_output()
        plot_burn_con_image()
        display(Label("Results saved successfully."))

# Your other function definitions and widget setup here

submit_button.on_click(on_submit_clicked)
adjust_button.on_click(on_adjust_clicked)
save_button.on_click(on_save_clicked)

# Create accordions for Fully Tile section
fully_tile_train_accordion_dNBR = VBox([
    burn_con_lv1_threshold_dnbr, 
    burn_con_lv3_threshold_dnbr, 
    burn_con_lv4_threshold_dnbr,
    fc, 
    submit_button, 
    folder_label, 
    # output_folder_input_pre, 
    # output_folder_input_after
])

fully_tile_train_accordion_rNDI = VBox([
    burn_con_lv1_threshold_rndi, 
    burn_con_lv3_threshold_rndi, 
    burn_con_lv4_threshold_rndi,
    fc, 
    submit_button, 
    folder_label, 
    # output_folder_input_pre, 
    # output_folder_input_after
])

fully_tile_predict = VBox([
    fc, 
    submit_button, 
    folder_label, 
    # output_folder_input_pre, 
    # output_folder_input_after
])

# Create accordions for AOI section
aoi_train_accordion_dNBR = VBox([
    burn_con_lv1_threshold_dnbr, 
    burn_con_lv3_threshold_dnbr, 
    burn_con_lv4_threshold_dnbr, 
    fc, 
    submit_button, 
    folder_label, 
    # output_folder_input_pre, 
    # output_folder_input_after
])

aoi_train_accordion_rNDI = VBox([
    burn_con_lv1_threshold_rndi, 
    burn_con_lv3_threshold_rndi, 
    burn_con_lv4_threshold_rndi,
    fc, 
    submit_button, 
    folder_label, 
    # output_folder_input_pre, 
    # output_folder_input_after
])

aoi_predict = VBox([
    fc, 
    submit_button, 
    folder_label, 
    # output_folder_input_pre, 
    # output_folder_input_after
])

# Fully Tile Accordion
fully_tile_accordion = Accordion(children=[fully_tile_train_accordion_dNBR, fully_tile_train_accordion_rNDI, fully_tile_predict])
fully_tile_accordion.set_title(0, 'dNBR : Differenced Normalized Burn Ratio')
fully_tile_accordion.set_title(1, 'rNDI : Relative Normalized Difference Index')
fully_tile_accordion.set_title(2, 'Predict')

# AOI Accordion
aoi_accordion = Accordion(children=[aoi_train_accordion_dNBR, aoi_train_accordion_rNDI, aoi_predict])
aoi_accordion.set_title(0, 'dNBR : Differenced Normalized Burn Ratio')
aoi_accordion.set_title(1, 'rNDI : Relative Normalized Difference Index')
aoi_accordion.set_title(2, 'Predict')

# Headers
header_full = VBox([widgets.HTML(value="<h1>Full Tile :</h1>")])
header_aoi= VBox([widgets.HTML(value="<h1>Area of Interest :</h1>")])

# Create main section tabs
fully_tile_tab = VBox([fully_tile_accordion])
aoi_tab = VBox([aoi_accordion])

section_tabs = Tab(children=[fully_tile_tab])
section_tabs.set_title(0, 'Full Tile')

section_tabs_aoi = Tab(children=[aoi_tab])
section_tabs_aoi.set_title(0, 'Area of Interest')

# Display the tabs
display(header_full, section_tabs, header_aoi, section_tabs_aoi,plot_burn_con_image(), output_widget) 