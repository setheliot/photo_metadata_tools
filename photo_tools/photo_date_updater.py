"""
Given a CSV file containing columns and data for Filename, Folder, and Set Date, 
this script will update the EXIF DateTimeOriginal field for each photo in the 
CSV file to the provided date in Set Date.

You can use the output file from photo_date_extractor.py as the input CSV file for this script.
This allows you to review the Set Dates in that file and adjust them before persisiting
the metadata into your photos.

This script does not support HEIC files.

Usage:
    python photo_updater.py --csv <csv_file>

Arguments:
    <csv_file>: The path to the CSV file containing the photo information.

Example:
    python photo_updater.py image_metadata.csv

Note: This script requires the `piexif` library, which can be installed using `pip install piexif`. Additionally, it assumes that the CSV file has columns named 'Folder', 'Filename', and 'Set Date' in the first row.
"""

import os
import sys
import piexif
from PIL import Image
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATE_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M"]
EXIF_DATE_FORMAT = '%Y:%m:%d %H:%M:%S'

def set_exif_date(file_path, set_date):
    """Set the EXIF DateTimeOriginal field to the provided date, only if it's not already set to that date. For JPEG, WebP and TIFF files"""
    try:
        # Load the existing EXIF data
        exif_dict = piexif.load(file_path)
        
        # Check if DateTimeOriginal is already set to the desired date
        current_date = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal)
        if current_date:
            current_date_str = current_date.decode('utf-8')
            if current_date_str[:10] == set_date[:10]:
                logger.info(f"EXIF DateTimeOriginal for {file_path} is already set to {set_date}. Skipping update.\n")
                return
        
        # Set the new DateTimeOriginal and DateTimeDigitized fields
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = set_date.encode('utf-8')
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = set_date.encode('utf-8')
        
        # Convert the EXIF dictionary back to bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Save the image with updated EXIF data
        piexif.insert(exif_bytes, file_path)
        logger.info(f"Updated EXIF DateTimeOriginal for {file_path} to {set_date}\n")
    
    except Exception as e:
        logger.error(f"Error updating EXIF data for {file_path}: {e}\n")

def set_exif_png_date(file_path, set_date):
    """Set the EXIF DateTimeOriginal field to the provided date for PNG files."""
    try:
        # Load the image
        with Image.open(file_path) as img:
            img.load()
        
            # Check if the image has an EXIF field
            if not hasattr(img, '_getexif'):
                logger.warning(f"No EXIF data found for {file_path}. Skipping update.\n")
                return
            
            # Get the existing EXIF data
            exif_dict = img.getexif()
            
            # Check if DateTimeOriginal is already set to the desired date
            current_date = exif_dict.get(piexif.ExifIFD.DateTimeOriginal)
            if current_date:
                current_date_str = current_date
                if current_date_str[:10] == set_date[:10]:
                    logger.info(f"EXIF DateTimeOriginal for {file_path} is already set to {set_date}. Skipping update.\n")
                    return
            
            # Set the new DateTimeOriginal and DateTimeDigitized fields
            exif_dict[piexif.ExifIFD.DateTimeOriginal] = set_date
            exif_dict[piexif.ExifIFD.DateTimeDigitized] = set_date
            
            # Save the image with updated EXIF data
            img.save(file_path, format="PNG", exif=exif_dict)
            logger.info(f"Updated EXIF DateTimeOriginal for {file_path} to {set_date}\n")
        
    except Exception as e:
        logger.error(f"Error updating EXIF data for {file_path}: {e}\n")

def normalize_date(date: str):
    """Try multiple date formats to parse the date string and return it in nomalized EXIF_DATE_FORMAT."""
    from datetime import datetime
    for date_format in DATE_FORMATS:
        try:
            valid_date = datetime.strptime(date, date_format)
            return valid_date.strftime(EXIF_DATE_FORMAT)
        except ValueError:
            continue
    return None

def process_csv(csv_file):
    """Process the CSV and update EXIF DateTimeOriginal for each photo."""
    import csv
    from datetime import datetime
    
    try:
        with open(csv_file, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                folder = row['Folder']
                filename = row['Filename']
                set_date = row['Set Date']
                
                if not set_date:
                    logger.warning(f"Set Date not found in CSV for file {filename}")
                    continue

                file_path = os.path.join(folder, filename)
                
                # Check if the file exists
                if os.path.exists(file_path):

                    # Validate against supported date format and return normalized date
                    valid_date = normalize_date(set_date)

                    if valid_date:
                        ext = os.path.splitext(file_path)[1].lower()

                        # Skip if the file is an HEIC
                        if ext=='.heic':
                            logger.warning(f"Skipping HEIC file: {file_path}\n")
                            continue
                        elif ext == '.png':
                            set_exif_png_date(file_path, valid_date)
                        elif ext in ['.jpg', '.jpeg', '.webp', '.tiff']:
                            set_exif_date(file_path, valid_date)
                        else:
                            logger.warning(f"Unsupported file format: {ext} for file {file_path}\n")
                    else:
                        logger.warning(f"Invalid date format for file {filename}: {set_date}\n")                                            
                else:
                    logger.warning(f"File not found: {file_path}")
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description='Update date time original in exif metadata for images.')
    parser.add_argument('csv_file', type=str, help='CSV file containing Set Date, Filename, Folder')
    args = parser.parse_args()
    if not os.path.exists(args.csv_file) or not os.path.isfile(args.csv_file):
        logger.error(f"Cannot find or access the csv_file provided: {args.csv_file}.")
        sys.exit(1)
    process_csv(args.csv_file)
    logger.info(f"CSV file {args.csv_file} processed.")

if __name__ == '__main__':
    main()

