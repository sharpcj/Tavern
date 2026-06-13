"""API views for registration, login status and admin review."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ReviewStatus
from .serializers import (
    AdminUserListSerializer,
    CurrentUserSerializer,
    RegisterSerializer,
    ReviewActionSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a pending account for identity review."""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(tags=["auth"])
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = CurrentUserSerializer(user, context=self.get_serializer_context()).data
        return Response(
            {
                "message": "注册申请已提交，请等待管理员审核。",
                "user": data,
            },
            status=status.HTTP_201_CREATED,
        )


class CurrentUserView(APIView):
    """Return the current user's account and review status."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=CurrentUserSerializer, tags=["auth"])
    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class PendingAccountListView(generics.ListAPIView):
    """List accounts that still need admin review attention."""

    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminUserListSerializer

    def get_queryset(self):
        return User.objects.filter(
            review_status__in=[ReviewStatus.PENDING, ReviewStatus.NEED_MORE_INFO]
        ).order_by("date_joined")

    @extend_schema(tags=["admin-accounts"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminReviewAccountView(APIView):
    """Apply an admin review decision to a user account."""

    permission_classes = [permissions.IsAdminUser]

    @extend_schema(request=ReviewActionSerializer, responses=AdminUserListSerializer, tags=["admin-accounts"])
    def post(self, request, account_id):
        user = generics.get_object_or_404(User, account_id=account_id)
        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update_user(user, request.user)
        return Response(AdminUserListSerializer(user).data)
