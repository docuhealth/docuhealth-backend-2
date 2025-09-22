from django.urls import path
from .views import CreateHospitalView

urlpatterns = [
    path('', CreateHospitalView.as_view(), name='create-hospital'),
]