"""Common API views used by the project foundation."""

from asgiref.sync import sync_to_async
from django.core import signing
from django.http import Http404, StreamingHttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.media_urls import MEDIA_SIGNING_SALT, MEDIA_URL_MAX_AGE_SECONDS
from apps.common.models import Media


class HealthCheckView(APIView):
    """Small unauthenticated health endpoint for local and deployment checks."""

    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="Service is alive.",
            )
        },
        tags=["common"],
    )
    def get(self, request):
        return Response({"status": "ok", "service": "tavern"})


class SignedMediaFileView(APIView):
    """Serve uploaded media only when a short-lived signed token is present."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(exclude=True)
    def get(self, request, pk: int):
        token = request.query_params.get("token", "")
        try:
            payload = signing.loads(token, salt=MEDIA_SIGNING_SALT, max_age=MEDIA_URL_MAX_AGE_SECONDS)
        except signing.BadSignature as exc:
            raise Http404 from exc
        if payload.get("media_id") != pk:
            raise Http404
        media = Media.objects.filter(pk=pk).first()
        if media is None or not media.file:
            raise Http404

        file_obj = media.file.open("rb")

        async def file_chunks():
            try:
                while True:
                    chunk = await sync_to_async(file_obj.read, thread_sensitive=True)(8192)
                    if not chunk:
                        break
                    yield chunk
            finally:
                await sync_to_async(file_obj.close, thread_sensitive=True)()

        response = StreamingHttpResponse(file_chunks(), content_type=media.content_type or "application/octet-stream")
        response["Content-Disposition"] = f'inline; filename="{media.original_name}"'
        response["Cache-Control"] = "private, max-age=300"
        response["X-Content-Type-Options"] = "nosniff"
        return response
