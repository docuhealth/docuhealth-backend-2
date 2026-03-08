from django.urls import path
from .views import AdminDashboard

urlpatterns = [
    path('/dashboard', AdminDashboard.as_view(), name='admin-dashboard'),
]