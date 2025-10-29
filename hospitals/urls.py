from django.urls import path
from .views import CreateHospitalView, CreateDoctorView, ListCreateHospitalInquiryView, ListCreateHospitalVerificationRequestView, ApproveVerificationRequestView

urlpatterns = [
    path('', CreateHospitalView.as_view(), name='create-hospital'),
    path('/doctors', CreateDoctorView.as_view(), name='create-doctor'),
    path('/inquiries', ListCreateHospitalInquiryView.as_view(), name='create-inquiry'),
    path('/verification-request', ListCreateHospitalVerificationRequestView.as_view(), name='list-create-verification-request'),
    path('/approve-verification', ApproveVerificationRequestView.as_view(), name='approve-verification-request'),
]