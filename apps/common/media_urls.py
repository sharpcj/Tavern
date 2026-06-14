"""Helpers for generating and resolving short-lived media access URLs."""

from __future__ import annotations

from urllib.parse import quote, urlparse

from django.conf import settings
from django.core import signing

from apps.common.models import Media

MEDIA_SIGNING_SALT = "tavern.media-access"
MEDIA_URL_MAX_AGE_SECONDS = 3600


def make_signed_media_token(media_id: int) -> str:
    """Return a signed token that authorizes temporary access to one media row."""
    return signing.dumps({"media_id": media_id}, salt=MEDIA_SIGNING_SALT)


def build_signed_media_url(media: Media, request=None) -> str:
    """Build a browser-loadable, short-lived media URL."""
    token = quote(make_signed_media_token(media.pk), safe="")
    path = f"/api/v1/media/{media.pk}/file/?token={token}"
    if request is not None:
        return request.build_absolute_uri(path)
    return path


def resolve_media_from_stored_url(url: str) -> Media | None:
    """Resolve legacy stored media URLs, such as /media/media/YYYY/MM/file.jpg, to Media."""
    if not url:
        return None
    parsed_path = urlparse(url).path or url
    normalized_path = parsed_path.lstrip("/")
    media_prefix = str(settings.MEDIA_URL).lstrip("/")
    if media_prefix and normalized_path.startswith(media_prefix):
        normalized_path = normalized_path[len(media_prefix):]
    return Media.objects.filter(file=normalized_path).first()


def sign_stored_media_url(url: str, request=None) -> str:
    """Convert a stored local media URL to a signed URL when possible."""
    media = resolve_media_from_stored_url(url)
    if media is None:
        return url
    return build_signed_media_url(media, request=request)
