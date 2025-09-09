from django.urls import path
from .views import PatientDashboardView, ListCreateSubaccountView, ListSubaccountMedicalRecordsView

urlpatterns = [
    path('dashboard', PatientDashboardView.as_view(), name='patient-dashboard'),
    path('subaccounts', ListCreateSubaccountView.as_view(), name='create-subaccount'),
    path('subaccounts/medical-records/<int:hin>', ListSubaccountMedicalRecordsView.as_view(), name='get-subaccount-medical-records'),
]