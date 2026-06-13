"""API views for birthday classmates and wishes."""

from __future__ import annotations

from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import AccountStatus, ReviewStatus, UserRole
from apps.common.enums import ContentStatus
from apps.common.permissions import IsApprovedClassmate
from apps.profiles.models import Profile

from .models import BirthdayWish
from .serializers import BirthdayClassmateSerializer, BirthdayWishCreateSerializer, BirthdayWishSerializer


def is_moderator_or_above(user) -> bool:
    return user.role in (UserRole.MODERATOR, UserRole.SUPER_ADMIN)


class CurrentMonthBirthdayListView(generics.ListAPIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = BirthdayClassmateSerializer

    def get_queryset(self):
        current_month = timezone.localdate().month
        return Profile.objects.select_related("user").filter(
            user__review_status=ReviewStatus.APPROVED,
            user__account_status=AccountStatus.NORMAL,
            birthday_month=current_month,
            show_birthday=True,
        )

    @extend_schema(tags=["birthdays"], responses=BirthdayClassmateSerializer)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BirthdayWishListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsApprovedClassmate]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BirthdayWishCreateSerializer
        return BirthdayWishSerializer

    def get_queryset(self):
        qs = BirthdayWish.objects.select_related("recipient", "author").filter(status=ContentStatus.PUBLISHED)
        recipient = self.request.query_params.get("recipient")
        if recipient:
            qs = qs.filter(recipient__account_id=recipient)
        return qs

    @extend_schema(
        tags=["birthdays"],
        parameters=[OpenApiParameter("recipient", str, description="按被祝福人 account_id 筛选")],
        responses=BirthdayWishSerializer,
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["birthdays"], request=BirthdayWishCreateSerializer, responses=BirthdayWishSerializer)
    def post(self, request, *args, **kwargs):
        serializer = BirthdayWishCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        wish = serializer.save()
        return Response(BirthdayWishSerializer(wish, context={"request": request}).data, status=status.HTTP_201_CREATED)


class BirthdayWishDeleteView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = BirthdayWishSerializer

    @extend_schema(tags=["birthdays"])
    def delete(self, request, pk: int):
        wish = generics.get_object_or_404(BirthdayWish, pk=pk)
        if wish.author != request.user and not is_moderator_or_above(request.user):
            return Response({"detail": "只有作者或管理员可以删除祝福"}, status=status.HTTP_403_FORBIDDEN)
        wish.soft_delete(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BirthdayWishHideView(APIView):
    permission_classes = [IsApprovedClassmate]
    serializer_class = BirthdayWishSerializer

    @extend_schema(tags=["birthdays"], responses=BirthdayWishSerializer)
    def post(self, request, pk: int):
        if not is_moderator_or_above(request.user):
            return Response({"detail": "只有管理员可以隐藏祝福"}, status=status.HTTP_403_FORBIDDEN)
        wish = generics.get_object_or_404(BirthdayWish, pk=pk)
        wish.status = ContentStatus.HIDDEN
        wish.save(update_fields=["status", "updated_at"])
        return Response(BirthdayWishSerializer(wish, context={"request": request}).data)
