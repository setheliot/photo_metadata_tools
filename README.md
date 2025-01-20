# Photo Metadata Tools

This project includes two Python scripts:
- `photo_date_extractor.py`: Given a folder, will iterate over all the photos to extract all date metadata into a CSV file.
- `photo_date_updater.py`: Given a CSV file containing will update the EXIF DateTimeOriginal field for each photo specified.

## Dependencies

The scripts rely on the following Python libraries:
- `piexif`
- `Pillow`
- `pyheif`

## Installation and Use

1. Clone the repository

1. [recommended] Create and activate a Python virtual environment. One way (but not the only way) to do this is:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

1. Install the dependencies:
   ```bash
   cd photo_tools
   pip install -r requirements.txt
   ```

1. Run the scripts:
   ```bash
   photo_date_extractor.py [-h] (-d <directory> | -f <input filename>) [-o <output filename>]
   ```
  * The extractor either
    * iterates over all photos in the directory given (and its sub-directories)
    * or, it iterates through all the filenames in the file supplied
  * Output is a CSV, It goes into the output filename suppled, or the filename `image_metadata.csv` by default

   Optionally open the output_file and make any changes to **Set Date**. The script attempts to pick the most sensible value, but can make mistakes.

   Then use the file as the input into the next script:

   ```bash
   python photo_date_updater.py --csv <csv_file>
   ```

## Safety first
- `photo_date_extractor.py` is read-only
- `photo_date_updater.py` will write to the EXIF metadata of the photos in the input file. Please ensure this is what you want to do before running this script.

[As a reminder](LICENSE), THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

We highly recommend you make bakup copies of your photos before running the `photo_date_updater.py` script on them, so you can determine if the script is making the appoprorpiate changes that you want.
