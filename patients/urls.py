from django.urls import path
from .views import PatientDashboardView, ListCreateSubaccountView

urlpatterns = [
    path('dashboard', PatientDashboardView.as_view(), name='patient-dashboard'),
    path('subaccounts', ListCreateSubaccountView.as_view(), name='create-subaccount'),
]