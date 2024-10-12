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

DATE_OUTPUT_FORMAT = '%Y-%m-%d %H:%M:%S'
EXIF_DATE_FORMAT = '%Y:%m:%d %H:%M:%S'

def extract_file_dates(file_path):
    """Extract file modified and created dates."""
    try:
        stat_info = os.stat(file_path)
        modified_time = datetime.fromtimestamp(stat_info.st_mtime)
        created_time = datetime.fromtimestamp(getattr(stat_info, 'st_birthtime', stat_info.st_ctime))
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
                    tag_name = TAGS.get(tag, tag) # https://exiv2.org/tags.html
                    if tag_name in ["DateTime", "DateTimeOriginal", "DateTimeDigitized"]:
                        dates[tag_name] = datetime.strptime(str(value), EXIF_DATE_FORMAT)
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
                    dates['DateTimeOriginal'] = datetime.strptime(exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode('utf-8'), EXIF_DATE_FORMAT)
                if piexif.ExifIFD.DateTimeDigitized in exif_dict["Exif"]:
                    dates['DateTimeDigitized'] = datetime.strptime(exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized].decode('utf-8'), EXIF_DATE_FORMAT)
                if piexif.ImageIFD.DateTime in exif_dict["0th"]:
                    dates['DateTime'] = datetime.strptime(exif_dict["0th"][piexif.ImageIFD.DateTime].decode('utf-8'), EXIF_DATE_FORMAT)
    except Exception as e:
        logger.error(f"Error reading HEIC metadata from {file_path}: {e}")

    return dates

  
def sane_date_or_string(date_or_str):
    """Check if the date string is a sane date or just a string"""
    if not date_or_str:
        return date_or_str
    elif isinstance(date_or_str, datetime):
        return sane_date(date_or_str)
    else:
        return date_or_str

def sane_date(date):
    """Enforce that the date is a sane date for photo metadata."""
    if not date:
        return None
    try:
        if date.year < 1800 or date.year > 2100:
            return None
        else:
            return date
    except ValueError:
        return None

# Extract date from the standard Apple iPhone filename format (e.g. 20210101_123456_iOS.jpg)
# or format y-m-d_h-m-s (e.g. 2021-01-01_12-34-56.jpg)
def extract_filename_date(filename):
    """Extract date from the standard Apple iPhone filename format."""
    DATE_FORMATS = ['%Y%m%d', '%Y-%m-%d', '%Y%m%d_%H%M%S', '%Y-%m-%d_%H-%M-%S']
    date_str = filename.replace(' ', '_').split('_')[0]
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, date_format)
        except ValueError:
            continue
    return None

def choose_more_precise_date(set_date, challenger_date):
    """Choose the more precise date between two datetime objects."""
    if not set_date or not challenger_date:
        return set_date or challenger_date

    if set_date.date() == challenger_date.date() and set_date.time() != challenger_date.time():
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

                # Extract date if embedded in filename
                filename_date = extract_filename_date(file)

                # Extract EXIF metadata or HEIC metadata
                exif_dates = {}
                if file.lower().endswith('.heic'):
                    exif_dates = extract_heic_metadata(file_path)
                else:
                    exif_dates = extract_exif_data(file_path)

                # Prepare the row for the CSV
                metadata = {
                    'Filename': file,
                    'File Extension': os.path.splitext(file)[1].lower(),
                    'Folder': root,
                }
                date_fields = {
                    'From Filename': filename_date,
                    'File Modified Date': modified_time,
                    'File Created Date': created_time,
                    'EXIF DateTime': exif_dates.get('DateTime', None),
                    'EXIF DateTimeOriginal': exif_dates.get('DateTimeOriginal', None),
                    'EXIF DateTimeDigitized': exif_dates.get('DateTimeDigitized', None),
                }

                # remove any dates that are not sane
                date_fields = {k: sane_date(v) for k, v in date_fields.items()}

                # Filter out None values and compute the earliest date
                set_date = min((v for v in date_fields.values() if v is not None), default=None)

                # Existing EXIF DateTimeOriginal is preferred if available and more precise than Set Date
                exif_date = date_fields['EXIF DateTimeOriginal']

                if exif_date:
                    set_date = choose_more_precise_date(set_date, exif_date)

                # Existing file modified date is preferred if available and more precise than Set Date
                if modified_time:
                    if set_date != exif_date:
                        set_date = choose_more_precise_date(set_date, modified_time)

                # Add the Set Date to the date fields
                date_fields['Set Date'] = set_date

                # Add date fields to metadata row
                metadata.update(date_fields)

                # Add row to metadata list
                metadata_list.append(metadata)
    
    return metadata_list

def save_to_csv(data, output_file):
    """Save the metadata to a CSV file."""
    headers = ['Filename', 'File Extension', 'Folder', 'From Filename', 'File Modified Date', 'File Created Date', 
               'EXIF DateTime', 'EXIF DateTimeOriginal', 'EXIF DateTimeDigitized', 'Set Date']

    try:
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            # Write the rows with dates formatted as strings
            for row in data:
                row = {k: (v.strftime(DATE_OUTPUT_FORMAT) if isinstance(v, datetime) else v) for k, v in row.items()}
                writer.writerows([row])
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
