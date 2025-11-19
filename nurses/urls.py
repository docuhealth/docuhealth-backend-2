from django.urls import path
from .views import NurseDashboardView, ListAdmissionRequestsView, ConfirmAdmissionView

urlpatterns = [
    path('/dashboard', NurseDashboardView.as_view(), name='nurse-dashboard'),
    path('/admissions/requests', ListAdmissionRequestsView.as_view(), name='admission-requests'),
    path('/admissions/<str:admission_id>/confirm', ConfirmAdmissionView.as_view(), name='admission-requests'),
]