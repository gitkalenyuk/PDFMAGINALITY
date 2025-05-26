from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register_user, name='register_user'),
    path('login', views.login_user, name='login_user'),
    path('logout', views.logout_user, name='logout_user'),
    path('password-reset-request', views.password_reset_request, name='password_reset_request'),
    path('password-reset-confirm', views.password_reset_confirm, name='password_reset_confirm'),
    path('profile', views.get_user_profile, name='get_user_profile'),
    path('profile/update', views.update_user_profile, name='update_user_profile'),
]
