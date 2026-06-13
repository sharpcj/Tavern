"""Custom DRF exception handler that returns structured error responses."""

from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def tavern_exception_handler(exc, context):
    """Wrap DRF's default handler to add structured error codes."""
    response = drf_exception_handler(exc, context)

    if response is not None and isinstance(exc, PermissionDenied):
        request = context.get("request")
        code = getattr(request, "_tavern_permission_code", None) if request else None
        if code is None:
            code = "PERMISSION_DENIED"
        message = _error_message(code)
        response.data = {"code": code, "message": message}
        response.status_code = status.HTTP_403_FORBIDDEN

    if response is not None and isinstance(exc, NotAuthenticated):
        response.data = {"code": "NOT_AUTHENTICATED", "message": "请先登录"}

    return response


def _error_message(code: str) -> str:
    messages = {
        "ACCOUNT_PENDING_REVIEW": "账号正在等待管理员审核，审核通过后才能访问内部内容。",
        "ACCOUNT_REJECTED": "账号审核未通过，如需申诉请联系管理员。",
        "ACCOUNT_NEED_MORE_INFO": "管理员需要你补充资料，请完善资料后重新提交审核。",
        "ACCOUNT_BANNED": "账号已被封禁，无法访问内部内容。",
        "ACCOUNT_RESTRICTED": "账号已被限制，当前操作不被允许。",
        "PERMISSION_DENIED": "你没有权限执行此操作。",
    }
    return messages.get(code, "访问被拒绝。")
