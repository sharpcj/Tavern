"""API views for profile management and classmate directory."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import AccountStatus, ReviewStatus
from apps.common.permissions import IsApprovedClassmate

from .models import Profile
from .serializers import (
    ClassmateDetailSerializer,
    ClassmateListSerializer,
    ProfileSerializer,
)

User = get_user_model()


class MyProfileView(APIView):
    """View or edit the current user's own profile."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=ProfileSerializer, tags=["profile"])
    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        return Response(ProfileSerializer(profile).data)

    @extend_schema(request=ProfileSerializer, responses=ProfileSerializer, tags=["profile"])
    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ClassmateListView(generics.ListAPIView):
    """Paginated classmate directory with search and filter."""

    permission_classes = [IsApprovedClassmate]
    serializer_class = ClassmateListSerializer

    def get_queryset(self):
        qs = Profile.objects.select_related("user").filter(
            user__review_status=ReviewStatus.APPROVED,
            user__account_status=AccountStatus.NORMAL,
        )

        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(user__real_name__icontains=search)
                | Q(city__icontains=search)
                | Q(occupation__icontains=search)
            )

        city = self.request.query_params.get("city", "").strip()
        if city:
            qs = qs.filter(city__iexact=city)

        occupation = self.request.query_params.get("occupation", "").strip()
        if occupation:
            qs = qs.filter(occupation__icontains=occupation)

        return qs.order_by("user__real_name")

    @extend_schema(
        tags=["classmates"],
        parameters=[
            OpenApiParameter("search", str, description="按姓名、城市、行业模糊搜索"),
            OpenApiParameter("city", str, description="按城市精确筛选"),
            OpenApiParameter("occupation", str, description="按行业模糊筛选"),
            OpenApiParameter("page", int, description="页码"),
            OpenApiParameter("page_size", int, description="每页条数"),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ClassmateDetailView(APIView):
    """View a single classmate's profile with visibility-filtered contact info."""

    permission_classes = [IsApprovedClassmate]

    @extend_schema(responses=ClassmateDetailSerializer, tags=["classmates"])
    def get(self, request, account_id):
        user = generics.get_object_or_404(
            User.objects.filter(
                review_status=ReviewStatus.APPROVED,
                account_status=AccountStatus.NORMAL,
            ),
            account_id=account_id,
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        serializer = ClassmateDetailSerializer(profile, viewer=request.user)
        return Response(serializer.data)
