import os

import cloudinary
import cloudinary.uploader


def _configure_cloudinary():
    settings = {
        'cloud_name': os.environ.get('CLOUDINARY_CLOUD_NAME'),
        'api_key': os.environ.get('CLOUDINARY_API_KEY'),
        'api_secret': os.environ.get('CLOUDINARY_API_SECRET')
    }
    if not all(settings.values()):
        raise RuntimeError('Cloudinary environment variables are not configured')
    cloudinary.config(**settings, secure=True)


def upload_item_image(image, public_id=None):
    _configure_cloudinary()
    upload_options = {
        'folder': 'preorder_app/items',
        'resource_type': 'image'
    }
    if public_id:
        upload_options.update({'public_id': public_id, 'overwrite': True})
    result = cloudinary.uploader.upload(image, **upload_options)
    return result['secure_url'], result['public_id']


def delete_item_image(public_id):
    if not public_id:
        return
    _configure_cloudinary()
    result = cloudinary.uploader.destroy(public_id, resource_type='image')
    if result.get('result') not in {'ok', 'not found'}:
        raise RuntimeError('Cloudinary did not remove the item image')