from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
import random
import string
from datetime import datetime, timedelta
from django.core.mail import send_mail
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from .utils import password_reset_token
import base64

verification_codes = {}

User = get_user_model()  # Use the custom user model

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(View):
    def post(self, request):
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Debugging: Print the received email and username
        print(f"Received email during registration: {email}")
        print(f"Received username during registration: {username}")

        # Check if email is provided
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)

        # Check if username is provided
        if not username:
            return JsonResponse({'error': 'Username is required'}, status=400)

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)

        # Generate a random 6-digit verification code
        code = ''.join(random.choices(string.digits, k=6))
        expiration_time = datetime.now() + timedelta(minutes=2)

        # Store the code and user data temporarily
        verification_codes[email] = {
            'code': code,
            'expiration': expiration_time,
            'username': username,
            'password': password,
        }

        # Debugging: Print the stored verification codes
        print(f"Stored verification codes: {verification_codes}")

        # Send the verification code via email
        send_mail(
            'Your Verification Code',
            f'Your verification code is: {code}',
            'syedalianza@gmail.com',  # Sender email
            [email],  # Recipient email
            fail_silently=False,
        )

        return JsonResponse({'message': 'Verification code sent to your email'}, status=200)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailView(View):
    def post(self, request):
        email = request.POST.get('email')
        code = request.POST.get('code')

        # Debugging: Print the received email and code
        print(f"Received email: {email}")
        print(f"Received code: {code}")
        print(f"Stored codes: {verification_codes}")

        # Check if the email exists in verification_codes
        if email not in verification_codes:
            print("Email not found in verification_codes")
            return JsonResponse({'error': 'Invalid code'}, status=400)

        # Check if the code matches
        if verification_codes[email]['code'] != code:
            print("Code does not match")
            return JsonResponse({'error': 'Invalid code'}, status=400)

        # Check if the code has expired
        if datetime.now() > verification_codes[email]['expiration']:
            print("Code has expired")
            return JsonResponse({'error': 'Code has expired'}, status=400)

        # Create the user
        user_data = verification_codes[email]
        user = User.objects.create_user(
            email=email,
            username=user_data['username'],
            password=user_data['password'],
        )

        # Clear the verification code
        del verification_codes[email]

        return JsonResponse({'message': 'User created successfully'}, status=201)


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