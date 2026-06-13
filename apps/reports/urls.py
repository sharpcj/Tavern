"""URL routes for reports."""

from django.urls import path

from .views import AdminReportDetailView, AdminReportHandleView, AdminReportListView, ReportCreateView

urlpatterns = [
    path("reports/", ReportCreateView.as_view(), name="report-create"),
    path("admin/reports/", AdminReportListView.as_view(), name="admin-report-list"),
    path("admin/reports/<int:pk>/", AdminReportDetailView.as_view(), name="admin-report-detail"),
    path("admin/reports/<int:pk>/handle/", AdminReportHandleView.as_view(), name="admin-report-handle"),
]
