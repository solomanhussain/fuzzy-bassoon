import os
import json
import logging
import exiftool
import subprocess
from shutil import copy2
from concurrent.futures import ThreadPoolExecutor

#logging.basicConfig(filename='/path/to/destination/directory/organize_photos.log', level=logging.INFO)
logger = logging.getLogger('file_organizer')
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


def get_video_date(file_path):
    try:
        result = subprocess.run(
            ['ffprobe', '-show_entries', 'format_tags=creation_time', '-v', 'quiet', '-of', 'csv=p=0', file_path],
            stdout=subprocess.PIPE, text=True
        )
        date_str = result.stdout.strip()
        return date_str.split(' ')[0]
    except Exception as e:
        logging.error(f'Failed to get date for {file_path}: {e}')
        return None

def process_file(file_path, dest_dir, dry_run=False):
    target_dir = None  # Define target_dir as None initially
    try:
        # Determine the file type and call the appropriate function to get the date
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.raf', '.nef', '.cr2', '.arw', '.orf', '.dcr', '.pef', '.rw2', '.3fr', '.iiq', '.erf', '.mef', '.mos')):
            date = get_date(file_path)
        elif file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            date = get_video_date(file_path)
        else:
            logging.info(f'Unrecognized file type for {file_path}')
            target_dir = os.path.join(dest_dir, 'Non-Image')

        if date:  # If a date was found
            date_parts = date.split(' ')[0].split(':')
            if len(date_parts) == 3:
                year, month, day = date_parts
                target_dir = os.path.join(dest_dir, year, f"{year}-{month}-{day}")
            else:
                logging.error(f'Unexpected date format for {file_path}: {date}')
                return
        
        if target_dir:  # Only proceed if target_dir has been defined
            os.makedirs(target_dir, exist_ok=True)
        
            target_path = os.path.join(target_dir, os.path.basename(file_path))
            target_path = handle_duplicates(target_path)
        
            move_file(file_path, target_path, dry_run)
        else:
            logging.warning(f'No target directory determined for {file_path}')

    except Exception as e:
        logging.error(f'Error processing {file_path}: {e}')


def organize_files(src_dir, dest_dir, dry_run=False):
    with ThreadPoolExecutor() as executor:
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.startswith("._"):
                    logging.info(f'Skipping AppleDouble file {file}')
                    continue
                file_path = os.path.join(root, file)
                executor.submit(process_file, file_path, dest_dir, dry_run)


src_dir = "/path/to/source/directory"
dest_dir = "/path/to/destination/directory"

dry_run = False  # Set to True for a dry-run
organize_files(src_dir, dest_dir, dry_run)
print('Done')