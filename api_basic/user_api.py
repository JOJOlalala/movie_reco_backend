# user login require
from django.contrib.auth.forms import UserCreationForm
from .interfaces.forms import LoginForm
from rest_framework_jwt.settings import api_settings
import json
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.views import refresh_jwt_token
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.


class userRegisterAPIView(APIView):

    # register
    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            # The first time user register need password verification, so use password1
            password = form.cleaned_data['password1']
            user = authenticate(request, username=username, password=password)
            login(request, user)
            # return token
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            return Response({'message': 'register success', 'data': {'token': token}}, status=status.HTTP_200_OK)
        else:
            # Return an 'invalid login' error message.
            return Response(form.errors, status=status.HTTP_401_UNAUTHORIZED)


class userLoginAPIView(APIView):
    # login
    # using this or using jwt original obtain_auth_api is both OK
    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            login(request, user)
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            # way to get user info through token
            # jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
            # jwt_decode_handler(token)
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            return Response({'message': 'login success', 'data': {'token': token}}, status=status.HTTP_200_OK)
        else:
            # Return an 'invalid login' error message.
            return Response(form.errors, status=status.HTTP_401_UNAUTHORIZED)


class userLogoutView(APIView):
    # logout
    # this fucntion can clear all the sessions on server side
    # you must first login will you able to logout
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        refresh_jwt_token(request)
        return Response({'message': 'logout success'}, status=status.HTTP_200_OK)


class UserProfile(models.Model):
    # 当生成 user 的时候自动生成 UserProfile，参考之前的 token 生成
    user = models.OneToOne(User, related_name="profile",
                           on_delete=models.CASCADE)
    phone_num = models.CharField(max_length=20, unique=True, blank=True)

    @receiver(post_save, sender=settings.AUTH_USER_MODEL)
    def create_profile(sender, instance=None, created=False, **kwargs):
        if created:
            profile, created = UserProfile.objects.get_or_create(user=instance)
