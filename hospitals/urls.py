from django.urls import path
from .views import CreateHospitalView, CreateDoctorView

urlpatterns = [
    path('', CreateHospitalView.as_view(), name='create-hospital'),
    path('/doctors', CreateDoctorView.as_view(), name='create-doctor'),
]