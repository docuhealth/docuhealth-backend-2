from django.urls import path
from .views import PatientDashboardView, ListCreateSubaccountView, ListSubaccountMedicalRecordsView, UpgradeSubaccountView, CreatePatientView, UpdatePatientView, ListAppointmentsView, DeletePatientAccountView

urlpatterns = [
    path('', CreatePatientView.as_view(), name='create-patient'),
    path('/dashboard', PatientDashboardView.as_view(), name='patient-dashboard'),
    path('/update', UpdatePatientView.as_view(), name='update-patient'),
    path('/delete', DeletePatientAccountView.as_view(), name='delete-patient'),
    path('/subaccounts', ListCreateSubaccountView.as_view(), name='create-subaccount'),
    path('/subaccounts/medical-records/<int:hin>', ListSubaccountMedicalRecordsView.as_view(), name='get-subaccount-medical-records'),
    path('/subaccounts/upgrade', UpgradeSubaccountView.as_view(), name='upgrade-subaccount'),
    path('/appointments', ListAppointmentsView.as_view(), name='get-appointments'),
]