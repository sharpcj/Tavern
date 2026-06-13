"""Root URL configuration for the Tavern API service."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.common.urls')),
    path('api/v1/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.profiles.urls')),
    path('api/v1/', include('apps.posts.urls')),
    path('api/v1/', include('apps.activities.urls')),
    path('api/v1/', include('apps.announcements.urls')),
    path('api/v1/', include('apps.albums.urls')),
    path('api/v1/', include('apps.birthdays.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
