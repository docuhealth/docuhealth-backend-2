from django.urls import path
from .views import LoginView, CustomTokenRefreshView, ForgotPassword, VerifyForgotPasswordOTPView, ResetPasswordView, ListUserView, VerifySignupOTPView, UpdatePasswordView

urlpatterns = [
    path('signup/verify-otp', VerifySignupOTPView.as_view(), name='verify-signup-otp'),
    path('login', LoginView.as_view(), name='user-login'),
    path('refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password', ForgotPassword.as_view(), name='forgot-password'),
    path('forgot-password/verify-otp', VerifyForgotPasswordOTPView.as_view(), name='verify-otp'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
    path('users/all', ListUserView.as_view(), name='users'),
    
   path('hospital-staff/password', UpdatePasswordView.as_view(), name="update-hospital-staff-password")
]