"""Upload validation helpers for media files."""

from __future__ import annotations

from django.core.exceptions import ValidationError

#: Maximum upload size in bytes (10 MB).
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

#: Allowed image MIME types.
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}


def validate_file_size(uploaded_file, max_size: int = MAX_UPLOAD_SIZE) -> None:
    """Raise ValidationError if *uploaded_file* exceeds *max_size* bytes."""
    if uploaded_file.size > max_size:
        raise ValidationError(f"文件大小不能超过 {max_size // (1024 * 1024)} MB")


def validate_image_type(uploaded_file) -> None:
    """Raise ValidationError if *uploaded_file* is not an allowed image type."""
    content_type = getattr(uploaded_file, "content_type", None)
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(f"不支持的图片格式: {content_type}")
