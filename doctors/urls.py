from django.urls import path
from .views import RequestVitalSignsView

urlpatterns = [
    path('/vital-signs/request', RequestVitalSignsView.as_view(), name='request-vital-signs'),
]