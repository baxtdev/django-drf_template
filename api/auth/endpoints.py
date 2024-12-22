from django.urls import path

from rest_registration.api.views.change_password import ChangePasswordView
from rest_registration.api.views.login import LoginView,LogoutView


from api.user.api import ResetPasswordAPIView,CheckingCodeAPIView,\
    GetResetPasswordCodeAPIView,RegisterAPIView,GoogleAuthAPIView,\
    LoginByCodeAPIView

urlpatterns = [
    path('change-password/', ChangePasswordView.as_view(), name='rest_register'),
    path('login/', LoginView.as_view(), name='user-login'),
    path('logout/',LogoutView.as_view(),name='user-logout'),
    path('reset-password/get/verify-code/<str:phone>',GetResetPasswordCodeAPIView.as_view(),name='reset-password-get-code'),
    path('send/verify-code/<int:code>',ResetPasswordAPIView.as_view(),name='reset-password'),
    path('chek/verify-code/<int:code>',CheckingCodeAPIView.as_view(),name="reset-password-chek-code"),
    path('register/',RegisterAPIView.as_view(),name="user-register"),
    path('google/',GoogleAuthAPIView.as_view(),name="user-auth-google"),
    path('login-by-code/<int:code>', LoginByCodeAPIView.as_view(), name='login_by_code'),  # new login view with pin code authentication
]