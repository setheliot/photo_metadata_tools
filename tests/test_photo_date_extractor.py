import unittest
from datetime import datetime
import os
import sys

# Add the path to the photo_tools module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'photo_tools'))

try:
    import photo_date_extractor as pde
except ImportError:
    log.error("Could not import photo_date_extractor module. Exiting.")
    sys.exit(1)

class TestPhotoDateExtractor(unittest.TestCase):

    def setUp(self):
        self.PATH_TO_TEST_PHOTOS = './tests/test_photos'
        self.EXPECTED_METADATA = {
            '20150329_183026659_iOS.jpg':{
                'Filename': '20150329_183026659_iOS.jpg',
                'File Extension': '.jpg',
                'Folder': self.PATH_TO_TEST_PHOTOS,
                'From Filename': datetime(2015, 3, 29, 0, 0),
                'File Modified Date': datetime(2015, 3, 29, 19, 46),
                'File Created Date': datetime(2024, 10, 12, 15, 44),
                'EXIF DateTime': datetime(2015, 3, 29, 19, 46),
                'EXIF DateTimeOriginal': datetime(2015, 3, 29, 9, 10),
                'EXIF DateTimeDigitized': datetime(2015, 3, 29, 9, 10),
                'Set Date': datetime(2015, 3, 29, 9, 10)
            },
            '2015-03-29_183026659.jpg' : {
                'Filename': '2015-03-29_183026659.jpg',
                'File Extension': '.jpg',
                'Folder': self.PATH_TO_TEST_PHOTOS,
                'From Filename': datetime(2015, 3, 29, 0, 0),
                'File Modified Date': datetime(2024, 10, 12, 15, 45),
                'File Created Date': datetime(2024, 10, 12, 15, 57),
                'EXIF DateTime': datetime(2015, 3, 29, 19, 46),
                'EXIF DateTimeOriginal': datetime(2015, 3, 29, 9, 10),
                'EXIF DateTimeDigitized': datetime(2015, 3, 29, 9, 10),
                'Set Date': datetime(2015, 3, 29, 9, 10)
            },
            '10150329_183026659_baddate.jpg' : {
                'Filename': '10150329_183026659_baddate.jpg',
                'File Extension': '.jpg',
                'Folder': self.PATH_TO_TEST_PHOTOS,
                'From Filename': None,
                'File Modified Date': datetime(2024, 10, 12, 15, 59),
                'File Created Date': datetime(2024, 10, 12, 15, 59),
                'EXIF DateTime': datetime(2015, 3, 29, 19, 46),
                'EXIF DateTimeOriginal': datetime(2015, 3, 29, 9, 10),
                'EXIF DateTimeDigitized': datetime(2015, 3, 29, 9, 10),
                'Set Date': datetime(2015, 3, 29, 9, 10)
            }
        }


    def test_collect_image_metadata(self):
        metadata = pde.collect_image_metadata(self.PATH_TO_TEST_PHOTOS)

        self.maxDiff = None

        for row in metadata:
            with self.subTest(filename=row['Filename']):
                # remove anything over minutes precision from all dates in row
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = value.replace(second=0, microsecond=0)

                expected = self.EXPECTED_METADATA[row['Filename']]
                output = f"\nMetadata row: {row}\nExpected: {expected}"
                self.assertEqual(row, expected, output)

if __name__ == '__main__':
    unittest.main()
