from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from accounts.views import UploadUserProfileImageView
from .api_urls import medical_records_urls, patient_urls, hospital_urls, subscription_urls, receptionist_urls, nurse_urls, doctor_urls
from organizations.urls import pharmacy_urls

urlpatterns = [
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='redoc'),
    path('api/raw', SpectacularAPIView.as_view(), name='schema'),
    path('api/redoc', SpectacularRedocView.as_view(url_name='schema'), name='swagger-ui'),
    path('admin', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/medical-records', include(medical_records_urls)),
    path('api/patients', include(patient_urls)),
    path('api/hospitals', include(hospital_urls)),
    path('api/subscriptions', include(subscription_urls)),
    path('api/receptionists', include(receptionist_urls)),
    path('api/nurses', include(nurse_urls)),
    path('api/doctors', include(doctor_urls)),
    path('api/pharmacy', include(pharmacy_urls)),
    path('api/users/profile-image', UploadUserProfileImageView.as_view(), name="upload-user-profile-image"),
]


