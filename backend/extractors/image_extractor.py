from PIL import Image
from PIL.ExifTags import TAGS

def extract_image_metadata(image_path):
    metadata = {}

    try:
        image = Image.open(image_path)
        exif = image.getexif()

        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            metadata[str(tag)] = str(value)

    except Exception as e:
        print("EXIF ERROR:", e)

    return metadata