"""
Given a folder, will iterate over all the photos in that folder and its sub-folders recursively
to extract all date metadata into a CSV file.

The output CSV file can be used as input into photo_date_updater.py to update the EXIF
date metadata of the photos to try to match the date the photo was taken.

Usage:
python script.py <folder_path> [-o <output_file>]

Arguments:
  <folder_path>   The path to the folder containing photos
  -o <output_file>   The output CSV file name (default: image_metadata.csv)

Example:
python script.py /path/to/photos -o my_dates.csv
"""

import os
import csv
import piexif
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
import pyheif
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_file_dates(file_path):
    """Extract file modified and created dates."""
    try:
        stat_info = os.stat(file_path)
        modified_time = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        created_time = datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        return modified_time, created_time
    except Exception as e:
        logger.error(f"Error extracting file dates from {file_path}: {e}")
        return None, None

def extract_exif_data(file_path):
    """Extract EXIF date metadata from the image if available."""
    dates = {}
    
    try:
        # Try to open file using PIL for EXIF data
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name in ["DateTime", "DateTimeOriginal", "DateTimeDigitized"]:
                        dates[tag_name] = str(value).replace(":","-",2)
    except Exception as e:
        logger.error(f"Error reading EXIF data from {file_path}: {e}")

    return dates

def extract_heic_metadata(file_path):
    """Extract HEIC metadata using pyheif and piexif."""
    dates = {}
    try:
        heif_file = pyheif.read(file_path)
        for metadata in heif_file.metadata or []:
            if metadata['type'] == 'Exif':
                # Convert the raw EXIF bytes data into a dictionary using piexif
                exif_dict = piexif.load(metadata['data'])
                # Extract relevant date information from the EXIF dictionary
                if piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
                    dates['DateTimeOriginal'] = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                if piexif.ExifIFD.DateTimeDigitized in exif_dict["Exif"]:
                    dates['DateTimeDigitized'] = exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized].decode('utf-8')
                if piexif.ImageIFD.DateTime in exif_dict["0th"]:
                    dates['DateTime'] = exif_dict["0th"][piexif.ImageIFD.DateTime].decode('utf-8')
    except Exception as e:
        logger.error(f"Error reading HEIC metadata from {file_path}: {e}")
    
    dates = {k: v.replace(":", "-", 2) for k, v in dates.items()}

    return dates

def extract_filename_date(filename):
    """Extract date from the standard Apple iPhone filename format."""
    date_str = filename.split('_')[0]
    date_str = date_str[:8]
    try:
        date_obj = datetime.strptime(date_str, '%Y%m%d')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        return None

def choose_more_precise_date(set_date, challenger_date):
    """Choose the more precise date between two date strings."""
    if not set_date or not challenger_date:
        return set_date or challenger_date
    
    set_date_time = set_date.split()
    challenger_date_time = challenger_date.split()

    if len(challenger_date_time) > 1:
        if set_date_time[0] == challenger_date_time[0] and (len(set_date_time)==1 or set_date_time[1] != challenger_date_time[1]):
            return challenger_date
        else:
            return set_date


def collect_image_metadata(directory):
    """Recursively iterate over the directory and extract metadata for image files."""
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.heic']
    metadata_list = []

    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in allowed_extensions):
                file_path = os.path.join(root, file)
                
                # Extract file system dates
                modified_time, created_time = extract_file_dates(file_path)
                
                # Extract from standard apple iphone filename
                filename_date = extract_filename_date(file)

                # Extract EXIF metadata or HEIC metadata
                exif_dates = {}
                if file.lower().endswith('.heic'):
                    exif_dates = extract_heic_metadata(file_path)
                else:
                    exif_dates = extract_exif_data(file_path)
                
                # 'Set Date' is the earliest of the retrieved dates
                set_date = min(filter(None, [filename_date, modified_time, created_time, exif_dates.get('DateTime'), 
                        exif_dates.get('DateTimeOriginal'), exif_dates.get('DateTimeDigitized')]))
                exif_date = exif_dates.get('DateTimeOriginal', '')

                # if set_date and exif_date are the same date but different times, then use exif_date for set_date
                # because exif date is more accurate
                set_date = choose_more_precise_date(set_date, exif_date)

                # same for modified date
                if set_date != exif_date:
                    set_date = choose_more_precise_date(set_date, modified_time)

                # if set_date has only date and no time, then add 0:00 time
                if len(set_date) == 10:
                    set_date += ' 00:00' 

                # Prepare the row for the CSV
                metadata = {
                    'Filename': file,
                    'Folder': root,
                    'From Filename' : filename_date,
                    'File Modified Date': modified_time,
                    'File Created Date': created_time,
                    'EXIF DateTime': exif_dates.get('DateTime', ''),
                    'EXIF DateTimeOriginal': exif_date,
                    'EXIF DateTimeDigitized': exif_dates.get('DateTimeDigitized', ''),
                    'Set Date': set_date
                }
                metadata_list.append(metadata)
    
    return metadata_list

def save_to_csv(data, output_file):
    """Save the metadata to a CSV file."""
    headers = ['Filename', 'Folder', 'From Filename', 'File Modified Date', 'File Created Date', 
               'EXIF DateTime', 'EXIF DateTimeOriginal', 'EXIF DateTimeDigitized', 'Set Date']
    
    try:
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
    except Exception as e:
        logger.error(f"Error saving data to CSV file {output_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Extract metadata from images in a directory.')
    parser.add_argument('directory', type=str, help='Directory path containing images')
    parser.add_argument('-o', '--output', type=str, default='image_metadata.csv', help='Output CSV file path')
    args = parser.parse_args()
    if not os.path.exists(args.directory) or not os.path.isdir(args.directory):
        logger.error("Invalid directory path provided.")
        sys.exit(1)
    metadata = collect_image_metadata(args.directory)
    save_to_csv(metadata, args.output)
    logger.info(f"Metadata extraction complete. Results saved to {args.output}.")

if __name__ == '__main__':
    main()


