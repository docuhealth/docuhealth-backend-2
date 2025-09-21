from django.urls import path
from .views import PatientDashboardView, ListCreateSubaccountView, ListSubaccountMedicalRecordsView, UpgradeSubaccountView, CreatePatientView, UpdatePatientView, UploadPatientProfileImageView

urlpatterns = [
    path('', CreatePatientView.as_view(), name='create-patient'),
    path('/dashboard', PatientDashboardView.as_view(), name='patient-dashboard'),
    path('/update', UpdatePatientView.as_view(), name='update-patient'),
    path('/subaccounts', ListCreateSubaccountView.as_view(), name='create-subaccount'),
    path('/subaccounts/medical-records/<int:hin>', ListSubaccountMedicalRecordsView.as_view(), name='get-subaccount-medical-records'),
    path('/subaccounts/upgrade', UpgradeSubaccountView.as_view(), name='upgrade-subaccount'),
    path('/profile-image', UploadPatientProfileImageView.as_view(), name='patient-profile-image'),
]