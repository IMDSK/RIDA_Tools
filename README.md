# Project Name

## Overview

This project provides tools and utilities for processing geospatial raster data. It includes functionalities for resampling, cropping, and analyzing raster images. The tools are designed to handle various preprocessing tasks needed for remote sensing data, such as satellite imagery.

## Features

- Resample raster images to different resolutions
- Crop raster images based on shapefiles
- Perform machine learning tasks such as clustering and prediction
- Support for various geospatial file formats

## Installation

Follow these steps to set up the development environment and install the required libraries.

### Step 1: Create a Virtual Environment (Optional but recommended)

Creating a virtual environment helps in managing dependencies and avoids conflicts.

```sh
python -m venv env

on windows

.\env\Scripts\activate

on MacOs

source env/bin/activate


pip install ipywidgets==7.7.2
pip install ipyfilechooser==0.6.0
pip install ipython==8.12.0
pip install numpy==1.24.3
pip install pandas==2.0.2
pip install matplotlib==3.7.1
pip install seaborn==0.12.2
pip install scikit-image==0.20.0
pip install rasterio==1.3.8
pip install geopandas==0.13.0
pip install shapely==2.0.1
pip install xmltodict==0.13.0
pip install gdal==3.6.2
pip install reverse_geocoder==1.5.1
pip install pycountry==22.3.5
pip install fiona==1.9.4
pip install pyproj==3.5.0
pip install scikit-learn==1.2.2
pip install sqlalchemy==2.0.15
pip install lightgbm==3.3.5
pip install pickle-mixin==1.0.2


Usage
Running the Tools
Activate the virtual environment (if not already activated):


on windows 
.\env\Scripts\activate

on macOS
source env/bin/activate
