from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import UserProfile # Import UserProfile

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            if not all([username, email, password]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)

            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Email already exists'}, status=400)

            user = User.objects.create_user(username=username, email=email, password=password)
            return JsonResponse({'message': 'User created successfully'}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
@login_required
def get_user_profile(request):
    if request.method == 'GET':
        user = request.user
        try:
            profile_data = {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'preferred_language': user.profile.preferred_language
            }
            return JsonResponse(profile_data, status=200)
        except UserProfile.DoesNotExist:
            return JsonResponse({'error': 'User profile not found.'}, status=404)
    else:
        return JsonResponse({'error': 'Only GET requests are allowed'}, status=405)

@csrf_exempt
@login_required
def update_user_profile(request):
    if request.method == 'PUT':
        user = request.user
        try:
            data = json.loads(request.body)
            
            # Update User model fields
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            
            new_email = data.get('email')
            if new_email and new_email != user.email:
                if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                    return JsonResponse({'error': 'Email already in use.'}, status=400)
                user.email = new_email
            
            new_password = data.get('password')
            if new_password:
                # Add password validation here if needed (e.g., length, complexity)
                user.set_password(new_password)
            
            user.save()

            # Update UserProfile model fields
            try:
                profile = user.profile
                profile.preferred_language = data.get('preferred_language', profile.preferred_language)
                profile.save()
            except UserProfile.DoesNotExist:
                # This should ideally not happen if signals are working correctly
                UserProfile.objects.create(user=user, preferred_language=data.get('preferred_language', 'uk'))
            
            return JsonResponse({'status': 'success', 'message': 'Profile updated successfully.'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e: # Catch other potential errors
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Only PUT requests are allowed'}, status=405)

@csrf_exempt
def password_reset_confirm(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            uidb64 = data.get('uidb64')
            token = data.get('token')
            new_password = data.get('new_password')

            if not all([uidb64, token, new_password]):
                return JsonResponse({'error': 'Missing uidb64, token, or new_password.'}, status=400)

            try:
                uid = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None

            if user is not None and default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return JsonResponse({'status': 'success', 'message': 'Password has been reset.'}, status=200)
            else:
                return JsonResponse({'error': 'Invalid token or UID.'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not all([username, password]):
                return JsonResponse({'error': 'Missing username or password'}, status=400)

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return JsonResponse({'status': 'success', 'message': 'Login successful'}, status=200)
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
@login_required
def logout_user(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'status': 'success', 'message': 'Logout successful'}, status=200)
    else:
        # While @login_required handles GET, explicitly state POST is preferred for logout actions.
        return JsonResponse({'error': 'Only POST requests are allowed for logout'}, status=405)

@csrf_exempt
def password_reset_request(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            if not email:
                return JsonResponse({'error': 'Email not provided.'}, status=400)

            try:
                user = User.objects.get(email=email, is_active=True)
            except User.DoesNotExist:
                # Do not reveal if the user does not exist or is not active
                return JsonResponse({'status': 'success', 'message': 'If an account with this email exists, a password reset link has been sent (simulated).'}, status=200)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            # For API testing, return token and uid. In production, send email.
            return JsonResponse({
                'status': 'success', 
                'message': 'Password reset token generated (simulation - normally sent via email).', 
                'uid': uid, 
                'token': token
            }, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
