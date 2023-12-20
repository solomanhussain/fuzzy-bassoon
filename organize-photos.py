import os
import json
import logging
import exiftool
from shutil import copy2  # Import copy2 to copy files along with metadata

#logging.basicConfig(filename='/path/to/destination/directory/organize_photos.log, level=logging.INFO)
logger = logging.getLogger('photo_organizer')
logger.setLevel(logging.INFO)

# Create a file handler to log to a file
file_handler = logging.FileHandler('/path/to/destination/directory/organize_photos.log')
file_handler.setLevel(logging.INFO)

# Create a formatter and set it for this handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(file_handler)

# Create a stream handler to log to console (in this case, the notebook)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Optionally set a formatter for this handler if you want formatted output
stream_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(stream_handler)

def get_date(file_path):
    with exiftool.ExifTool() as et:
        metadata_json = et.execute(b'-j', file_path)
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)[0]
                return metadata.get("EXIF:DateTimeOriginal", None)
            except json.JSONDecodeError:
                logger.error(f'Failed to decode JSON metadata for {file_path}')
        else:
            logger.warning(f'No metadata returned for {file_path}')

def move_file(src, dest, dry_run=False):
    dest_dir = os.path.dirname(dest)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
    if os.path.exists(src) and os.access(src, os.R_OK):
        if not dry_run:
            copy2(src, dest)  # Use copy2 to copy file and metadata, then remove the source file
            os.remove(src)
        logger.info(f'Moved {src} to {dest}')
    else:
        logger.error(f'File {src} does not exist or is not accessible')

def handle_duplicates(file_path):
    base, ext = os.path.splitext(file_path)
    i = 1
    while os.path.exists(file_path):
        file_path = f"{base}_{i}{ext}"
        i += 1
    return file_path

def organize_photos(src_dir, dest_dir, dry_run=False):
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.startswith("._"):
                logger.info(f'Skipping AppleDouble file {file}')
                continue
            file_path = os.path.join(root, file)
            try:
                date = get_date(file_path)
                if date:
                    date_parts = date.split(' ')[0].split(':')
                    if len(date_parts) == 3:
                        year, month, day = date_parts
                        target_dir = os.path.join(dest_dir, year, f"{year}-{month}-{day}")
                    else:
                        logger.error(f'Unexpected date format for {file_path}: {date}')
                        continue
                elif file.lower().endswith(('.png', '.jpg', '.jpeg', '.raf', '.nef', '.cr2', '.arw', '.orf', '.dcr', '.pef', '.rw2', '.3fr', '.iiq', '.erf', '.mef', '.mos')):
                    target_dir = os.path.join(dest_dir, 'Dateless')
                else:
                    target_dir = os.path.join(dest_dir, 'Non-Image')
                
                os.makedirs(target_dir, exist_ok=True)
                
                target_path = os.path.join(target_dir, file)
                target_path = handle_duplicates(target_path)
                
                move_file(file_path, target_path, dry_run)
            
            except Exception as e:
                logger.error(f'Error processing {file_path}: {e}')

src_dir = "/path/to/source/directory"
dest_dir = "/path/to/destination/directory"

dry_run = False  # Set to True for a dry-run
organize_photos(src_dir, dest_dir, dry_run)
print('Done')