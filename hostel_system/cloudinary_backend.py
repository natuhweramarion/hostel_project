"""
Minimal Django 5-compatible Cloudinary media storage backend.

Uses the cloudinary Python SDK (pycloudinary) upload/API directly.
Does NOT override collectstatic and does NOT reference STATICFILES_STORAGE,
so it is fully compatible with Django 4.2+ / 5.x.

Configure via the CLOUDINARY_URL environment variable:
    cloudinary://API_KEY:API_SECRET@CLOUD_NAME
"""

import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class CloudinaryMediaStorage(Storage):

    def _save(self, name, content):
        public_id = self._public_id(name)
        cloudinary.uploader.upload(
            content,
            public_id=public_id,
            resource_type='auto',
            overwrite=True,
        )
        return name

    def url(self, name):
        if not name:
            return ''
        return cloudinary.CloudinaryImage(self._public_id(name)).build_url(secure=True)

    def exists(self, name):
        try:
            cloudinary.api.resource(self._public_id(name))
            return True
        except Exception:
            return False

    def delete(self, name):
        try:
            cloudinary.uploader.destroy(self._public_id(name))
        except Exception:
            pass

    def size(self, name):
        try:
            result = cloudinary.api.resource(self._public_id(name))
            return result.get('bytes', 0)
        except Exception:
            return 0

    def _open(self, name, mode='rb'):
        raise NotImplementedError('CloudinaryMediaStorage is write-only.')

    @staticmethod
    def _public_id(name):
        """Strip extension so Cloudinary doesn't double-append it."""
        return os.path.splitext(name)[0].replace('\\', '/')
