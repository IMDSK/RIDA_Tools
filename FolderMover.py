import os
import shutil

def move_folders(base_path):
    image_pre_path = os.path.join(base_path, "Image_Pre")
    image_path = os.path.join(base_path, "Image")
    if not os.path.exists(image_pre_path):
        os.makedirs(image_pre_path)
    if not os.path.exists(image_path):
        os.makedirs(image_path)
    
    before_cropped_path = os.path.join(base_path, "Before_Cropped")
    after_cropped_path = os.path.join(base_path, "After_Cropped")

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
