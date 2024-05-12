import os

# Define the required jp2 files globally
REQUIRED_FILES = [
    "B02_10m.jp2", "B03_10m.jp2", "B04_10m.jp2", "B08_10m.jp2",
    "B05_20m.jp2", "B06_20m.jp2", "B07_20m.jp2", "B8A_20m.jp2",
    "B09_60m.jp2", "B12_20m.jp2"
]

def check_files_in_directory(directory):
    existing_files = os.listdir(directory)
    missing_files = [file for file in REQUIRED_FILES if not any(f.endswith(file) for f in existing_files)]
    return missing_files

def process_files(selected_folder):
    before_path = os.path.join(selected_folder, 'Before')
    after_path = os.path.join(selected_folder, 'After')

    missing_before = check_files_in_directory(before_path)
    missing_after = check_files_in_directory(after_path)

    if missing_before or missing_after:
        response = "Missing files detected:"
        if missing_before:
            response += f"\n'Before' folder missing: {', '.join(missing_before)}"
        if missing_after:
            response += f"\n'After' folder missing: {', '.join(missing_after)}"
    else:
        response = "All required files are present in both 'Before' and 'After' folders."
    return response
