"""Display-name helpers for content objects with DisplayMode."""

from __future__ import annotations

from apps.common.enums import DisplayMode


def get_display_name(obj) -> str:
    """Return the display name for a content object based on its display_mode.

    Expects *obj* to have ``display_mode`` and ``author`` attributes.
    """
    if obj.display_mode == DisplayMode.NICKNAME and getattr(obj.author, "nickname", None):
        return obj.author.nickname
    return obj.author.real_name
