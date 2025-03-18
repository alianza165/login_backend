from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views import View
import random
import string
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Store verification codes in memory (use a database in production)
verification_codes = {}

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(View):
    def post(self, request):
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')

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

        # Send the verification code via email
        send_mail(
            'Your Verification Code',
            f'Your verification code is: {code}',
            'syedalianza@gmail.com',  # Replace with your email
            ['syedalianza@gmail.com'],
            fail_silently=False,
        )
        # send_mail(
        #     'Test Subject',
        #     'Test message body.',
        #     'syedalianza@gmail.com',  # Sender email
        #     ['syedalianza@gmail.com'],  # Recipient email
        #     fail_silently=False,
        # )

        return JsonResponse({'message': 'Verification code sent to your email'}, status=200)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailView(View):
    def post(self, request):
        email = request.POST.get('email')
        code = request.POST.get('code')

        # Check if the email and code match
        if email not in verification_codes or verification_codes[email]['code'] != code:
            return JsonResponse({'error': 'Invalid code'}, status=400)

        # Check if the code has expired
        if datetime.now() > verification_codes[email]['expiration']:
            return JsonResponse({'error': 'Code has expired'}, status=400)

        # Create the user
        user_data = verification_codes[email]
        user = User.objects.create_user(
            username=user_data['username'],
            email=email,
            password=user_data['password'],
        )

        # Clear the verification code
        del verification_codes[email]

        return JsonResponse({'message': 'User created successfully'}, status=201)