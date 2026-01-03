import requests
import zipfile
from pathlib import Path
import os
import shutil


GTFS_URL = 'https://gtfs.mot.gov.il/gtfsfiles/israel-public-transportation.zip'
GTFS_FILE_NAME = "gtfs.zip"
GTFS_DIR = "./gtfs_data/"

#get the file from the url
response = requests.get(GTFS_URL, stream=True)
response.raise_for_status()

total_data_size = int(response.headers.get("Content_Length", 0))
downloded_data_size = 0
chunk_size = 1024 * 1024 #1MB 


#open a new file/overide existing
#load the data from the url to the file in chunks
with open(GTFS_DIR + GTFS_FILE_NAME, "wb") as gtfs_file:
    for chunk in response.iter_content(chunk_size=chunk_size):
        if not chunk:
            continue

        gtfs_file.write(chunk)
        downloded_data_size += len(chunk)

        if total_data_size:
            downloaded_percent = (downloded_data_size / total_data_size) * 100
            

            bar_length = 30
            filled_length = int(bar_length * downloaded_percent / 100)
            bar = "█" * filled_length + "-" * (bar_length - filled_length)

            #printing progress bar
            print(f"\rDownloading |{bar}| {downloaded_percent:5.1f}% ({downloded_data_size / 1024 / 1024 :.1f}/{total_data_size / 1024 /1024:.1f} MB)", end="")

        else:
            print(f"\rDownloaded {downloded_data_size / 1024 / 1024:.1f} MB", end="")

print("\nGTFS file successfuly downloaded.")


zip_path = Path(GTFS_DIR + GTFS_FILE_NAME)
extract_dir = Path(GTFS_DIR + "/gtfs_extracted_data")
extract_dir.mkdir(exist_ok=True)

##clear ectract directory (if existed)##
directory_to_clear = extract_dir

# 1. Delete the entire directory and its contents
if os.path.exists(directory_to_clear):
    shutil.rmtree(directory_to_clear)

# 2. Recreate the empty directory
os.mkdir(directory_to_clear)

with zipfile.ZipFile(zip_path, "r") as zip_ref:
    zip_ref.extractall(extract_dir)

print(f"ZIP extracted to {extract_dir}")
