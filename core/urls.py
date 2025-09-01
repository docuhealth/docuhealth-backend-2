from django.urls import path
from .views import CreateUserView, LoginView, CustomTokenRefreshView, ForgotPassword, VerifyLoginOTPView, ResetPasswordView, ListDeleteUserView, VerifyEmailOTPView

urlpatterns = [
    # path('<str:email>', ListDeleteUserView.as_view(), name='users'),
    path('signup', CreateUserView.as_view(), name='user-signup'),
    path('signup/verify-otp', VerifyEmailOTPView.as_view(), name='verify-signup-otp'),
    path('login', LoginView.as_view(), name='user-login'),
    path('refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password', ForgotPassword.as_view(), name='forgot-password'),
    path('forgot-password/verify-otp', VerifyLoginOTPView.as_view(), name='verify-otp'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
]