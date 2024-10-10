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
   python photo_date_extractor.py <folder_path> [-o <output_file>]
   ```
   Optionally open the output_file and make any changes to **Set Date**. The script attempts to pick the most sensible value, but can make mistakes.

   Then use the file as the input into the next script:

   ```bash
   python photo_date_updater.py --csv <csv_file>
   ```

- `photo_date_extractor.py` is read-only
- `photo_date_updater.py` will write to the EXIF metadata of the photos in the input file. Please ensure this is what you want to do before running this script.