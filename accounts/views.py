from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
import random
import string
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from .utils import password_reset_token
import base64
import json
import uuid

verification_codes = {}
pending_users = {}

User = get_user_model()  # Use the custom user model

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(View):
    def post(self, request):
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if the user already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'User with this email already exists'}, status=400)

        # Generate a verification token
        verification_token = str(uuid.uuid4())
        expiry = timezone.now() + timedelta(hours=24)  # Token expires in 24 hours

        # Save the user data and token temporarily (e.g., in a PendingUser model or cache)
        # For simplicity, we'll use a dictionary (in production, use a database or cache)
        pending_users[email] = {
            'username': username,
            'password': password,
            'token': verification_token,
            'expiry': expiry,
        }

        # Create the verification link
        verification_url = f"http://localhost:3000/verify-email/{urlsafe_base64_encode(force_bytes(email))}/{verification_token}/"

        # Send the verification email
        send_mail(
            'Verify Your Email',
            f'Click the link to verify your email: {verification_url}',
            'syedalianza@gmail.com',  # Sender email
            [email],  # Recipient email
            fail_silently=False,
        )

        return JsonResponse({'message': 'Verification link sent to your email'}, status=200)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailView(View):
    def get(self, request, uidb64, token):
        try:
            email = force_str(urlsafe_base64_decode(uidb64))
        except (TypeError, ValueError, OverflowError):
            return JsonResponse({'error': 'Invalid link'}, status=400)

        # Check if the email exists in pending_users
        if email not in pending_users:
            return JsonResponse({'error': 'Invalid or expired link'}, status=400)

        user_data = pending_users[email]

        # Check if the token matches and is not expired
        if user_data['token'] != token or timezone.now() > user_data['expiry']:
            return JsonResponse({'error': 'Invalid or expired link'}, status=400)

        # Create the user
        user = User.objects.create_user(
            email=email,
            username=user_data['username'],
            password=user_data['password'],
        )

        # Clear the pending user data
        del pending_users[email]

        return JsonResponse({'message': 'Email verified successfully'}, status=200)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetRequestView(View):
    def post(self, request):
        email = request.POST.get('email')
        print("Email:", email)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User with this email does not exist'}, status=400)

        # Generate a password reset token
        token = password_reset_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Create the password reset link
        reset_url = f"http://localhost:3000/reset-password/{uid}/{token}/"

        # Send the password reset email
        send_mail(
            'Password Reset Request',
            f'Click the link to reset your password: {reset_url}',
            'noreply@yourdomain.com',  # Sender email
            [email],  # Recipient email
            fail_silently=False,
        )

        return JsonResponse({'message': 'Password reset link sent to your email'}, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetConfirmView(View):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return JsonResponse({'error': 'Invalid user'}, status=400)

        # Verify the token
        if not password_reset_token.check_token(user, token):
            return JsonResponse({'error': 'Invalid or expired token'}, status=400)

        # Update the user's password
        new_password = request.POST.get('new_password')
        user.set_password(new_password)
        user.save()

        return JsonResponse({'message': 'Password reset successful'}, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class GoogleLoginView(View):
    def post(self, request):
        # Parse the request body as JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        email = data.get('email')
        name = data.get('name')

        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)

        try:
            # Check if the email is already registered
            user = User.objects.get(email=email)
            return JsonResponse({'error': 'Email already exists. Please log in using your credentials.'}, status=400)
        except User.DoesNotExist:
            # Create a new user
            username = email.split('@')[0]  # Use email prefix as username
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))  # Generate a random password
            user = User.objects.create_user(
                email=email,
                username=username,
                password=password,
                first_name=name,
            )

            # Generate tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)

            return JsonResponse({
                'access': access,
                'refresh': str(refresh),
                'username': user.username,
            }, status=200)