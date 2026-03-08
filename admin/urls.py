from django.urls import path
from .views import AdminDashboard, ListUsersView, DeactivateHospitalView, DeactivatePatientsView, ReactivateHospitalView, ReactivatePatientsView

urlpatterns = [
    path('/dashboard', AdminDashboard.as_view(), name='admin-dashboard'),
    path('/users/<str:role>', ListUsersView.as_view(), name='list-users'),
    
    path('/patients/deactivate', DeactivatePatientsView.as_view(), name="deactivate-patients"),
    path('/patients/activate', ReactivatePatientsView.as_view(), name="activate-patients"),
    path('/hospitals/deactivate', DeactivateHospitalView.as_view(), name="deactivate-hospitals"),
    path('/hospitals/activate', ReactivateHospitalView.as_view(), name="activate-hospitals"),
]