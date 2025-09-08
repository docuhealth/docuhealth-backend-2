from django.urls import path
from .views import PatientDashboardView, CreateSubaccountView

urlpatterns = [
    path('dashboard', PatientDashboardView.as_view(), name='patient-dashboard'),
    path('subaccounts', CreateSubaccountView.as_view(), name='create-subaccount'),
]