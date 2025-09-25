from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from core.views import UploadUserProfileImageView

urlpatterns = [
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='redoc'),
    path('api/raw', SpectacularAPIView.as_view(), name='schema'),
    path('api/redoc', SpectacularRedocView.as_view(url_name='schema'), name='swagger-ui'),
    path('admin', admin.site.urls),
    path('api/auth/', include('core.urls')),
    path('api/medical-records/', include('medicalrecords.urls')),
    path('api/patients', include('patients.urls')),
    path('api/hospitals', include('hospitals.urls')),
    path('api/users/profile-image', UploadUserProfileImageView.as_view(), name="upload-user-profile-image"),
]
