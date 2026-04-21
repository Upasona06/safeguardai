"""
CloudinaryService — wraps cloudinary SDK for file uploads.
All media and PDFs are stored here; only URL + public_id are kept in DB.
"""

import asyncio
import logging
import os
import tempfile
import time
from io import BytesIO

import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.utils

from backend.config.settings import settings

logger = logging.getLogger(__name__)

                               
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


class CloudinaryService:
    def raw_resource_exists(self, public_id: str) -> bool:
        """Check whether a raw upload resource exists in Cloudinary."""
        try:
            cloudinary.api.resource(public_id, resource_type="raw", type="upload")
            return True
        except Exception:
            return False

                                                                    
    async def upload_bytes(
        self,
        file_bytes: bytes,
        folder: str = "evidence",
        filename: str = "upload",
    ) -> str:
        """Upload image bytes to Cloudinary; return secure URL."""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._sync_upload_bytes,
            file_bytes,
            folder,
            filename,
        )

    def _sync_upload_bytes(self, file_bytes: bytes, folder: str, filename: str) -> str:
        try:
            result = cloudinary.uploader.upload(
                BytesIO(file_bytes),
                folder=folder,
                public_id=os.path.splitext(filename)[0],
                resource_type="image",
                overwrite=False,
                unique_filename=True,
            )
            url = result.get("secure_url", "")
            logger.info("Cloudinary upload OK: %s", url)
            return url
        except Exception as e:
            logger.error("Cloudinary upload failed: %s", e)
            return ""

                                                                    
    async def upload_file(
        self,
        file_path: str,
        folder: str = "fir_reports",
        resource_type: str = "raw",
        public_id: str | None = None,
    ) -> str:
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._sync_upload_file,
            file_path,
            folder,
            resource_type,
            public_id,
        )

    def _sync_upload_file(
        self,
        file_path: str,
        folder: str,
        resource_type: str,
        public_id: str | None,
    ) -> str:
        try:
            kwargs: dict = {
                "folder": folder,
                "resource_type": resource_type,
                "overwrite": True,
            }
            if public_id:
                kwargs["public_id"] = public_id

            result = cloudinary.uploader.upload(file_path, **kwargs)
            url = result.get("secure_url", "")
            logger.info("Cloudinary file upload OK: %s", url)
            return url
        except Exception as e:
            logger.error("Cloudinary file upload failed: %s", e)
            return ""

    def build_signed_raw_download_url(
        self,
        public_id: str,
        expires_in_seconds: int = 3600,
        filename: str | None = None,
    ) -> str:
        """
        Build a signed URL for raw asset download.
        Useful when direct raw URLs return 401 due account delivery restrictions.
        """
        try:
            expires_at = int(time.time()) + max(expires_in_seconds, 60)
            url = cloudinary.utils.private_download_url(
                public_id,
                "pdf",
                resource_type="raw",
                type="upload",
                expires_at=expires_at,
                attachment=True,
                filename=filename,
            )
            logger.info("Cloudinary signed raw download URL generated for: %s", public_id)
            return url
        except Exception as e:
            logger.warning("Failed to generate signed Cloudinary URL for %s: %s", public_id, e)
            return ""
