"""Common API views used by the project foundation."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


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
