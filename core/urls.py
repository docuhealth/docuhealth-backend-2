from django.urls import path
from .views import UserListCreateView, LoginView, CustomTokenRefreshView, ForgotPassword, VerifyOTPAndGetTokenView, ResetPasswordView

urlpatterns = [
    path('signup', UserListCreateView.as_view(), name='user-signup'),
    path('login', LoginView.as_view(), name='user-login'),
    path('refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password', ForgotPassword.as_view(), name='forgot-password'),
    path('verify-otp', VerifyOTPAndGetTokenView.as_view(), name='verify-otp'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
]