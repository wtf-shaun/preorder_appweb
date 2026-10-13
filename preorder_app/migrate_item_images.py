import argparse
import hashlib
from pathlib import Path

from app.db import items_col
from app.utils.image_storage import upload_item_image


PROJECT_DIR = Path(__file__).resolve().parent
UPLOAD_DIRS = [
    PROJECT_DIR / 'static' / 'uploads',
    PROJECT_DIR / 'app' / 'static' / 'uploads'
]


def find_local_image(image_value):
    filename = Path(str(image_value).replace('\\', '/')).name
    return next(
        (folder / filename for folder in UPLOAD_DIRS if (folder / filename).is_file()),
        None
    )


def migrate_images(apply_changes=False):
    migrated = 0
    skipped = 0
    failed = 0

    for item in items_col.find({'image': {'$type': 'string'}}):
        image_value = item['image']
        if image_value.startswith(('http://', 'https://')):
            skipped += 1
            continue

        local_image = find_local_image(image_value)
        if not local_image:
            print(f"MISSING {item.get('id')}: {image_value}")
            failed += 1
            continue

        print(f"{'UPLOAD' if apply_changes else 'WOULD UPLOAD'} {item.get('id')}: {local_image}")
        if not apply_changes:
            continue

        item_key = str(item.get('id', item['_id']))
        stable_id = 'legacy-' + hashlib.sha256(item_key.encode()).hexdigest()[:24]
        try:
            image_url, public_id = upload_item_image(local_image, public_id=stable_id)
            result = items_col.update_one(
                {'_id': item['_id'], 'image': image_value},
                {'$set': {'image': image_url, 'image_public_id': public_id}}
            )
            if result.modified_count:
                migrated += 1
            else:
                print(f"UNCHANGED {item.get('id')}: database image changed during upload")
                skipped += 1
        except Exception as error:
            print(f"FAILED {item.get('id')}: {error}")
            failed += 1

    print(f"Finished: {migrated} migrated, {skipped} skipped, {failed} failed")
    return failed == 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Migrate local menu item images to Cloudinary.'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Upload images and update MongoDB. Without this flag, only preview.'
    )
    args = parser.parse_args()
    raise SystemExit(0 if migrate_images(apply_changes=args.apply) else 1)