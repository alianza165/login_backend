from django.urls import path
from .views import RegisterView, VerifyEmailView, CustomTokenObtainPairView, PasswordResetRequestView, PasswordResetConfirmView, GoogleLoginView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/<str:uidb64>/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('google-login/', GoogleLoginView.as_view(), name='google_login'),
]