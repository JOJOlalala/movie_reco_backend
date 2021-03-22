from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.settings import api_settings
from rest_framework.decorators import action

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist

from .interfaces.forms import LoginForm, UserForm, UserProfileForm
from .permissions import IsAdminOrIsSelf
from .serializers import UserSerializer, UserProfileSerializer
from .interfaces.errorCode.userErrorCode import UserErrorCode


class UserViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, mixins.UpdateModelMixin, IsAdminOrIsSelf):
    """
    Example empty viewset demonstrating the standard
    actions that will be handled by a router class.

    If you're using format suffixes, make sure to also include
    the `format=None` keyword argument for each action.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrIsSelf]
    authentication_classes = [JSONWebTokenAuthentication]

    # if retrieve user only by user self or by admin
    lookup_field = "username"

    # def list(self, request):
    #     pass

    # def create(self, request):
    #     pass

    # def retrieve(self, request, pk=None):
    #     pass

    # def update(self, request, pk=None):
    #     pass

    # def partial_update(self, request, pk=None):
    #     pass

    # def destroy(self, request, pk=None):
    #     pass

    @action(detail=False, methods=['get'])
    def get_current_user(self, request):
        currentUser = request.user
        if currentUser.is_anonymous:
            return Response({'error': {'code': UserErrorCode.unknown_user.value}, 'message': '没有找到相应的用户', }, status=status.HTTP_400_BAD_REQUEST)
        userProfile = currentUser.profile
        userData = UserSerializer(currentUser).data
        userProfileData = UserProfileSerializer(userProfile).data
        return Response({
            'message': '成功获取用户信息',
            'data': {
                'userData': userData,
                'userProfileData': userProfileData
            }}, status=status.HTTP_200_OK)

    # note the permission is allowAny because everyone could be able to register
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            # The first time user register need password verification, so use password1
            password = form.cleaned_data['password1']
            user = authenticate(
                request, username=username, password=password)
            login(request, user)
            # return token
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            return Response({'message': '注册成功', 'data': {'token': token}}, status=status.HTTP_200_OK)
        else:
            # Return an 'invalid login' error message.
            return Response({'error': {'code': UserErrorCode.user_already_exist.value, 'message': form.errors}}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response({'message': '登出成功'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                User.objects.get(username=username)
            except ObjectDoesNotExist:
                return Response({'error': {'code': UserErrorCode.unknown_user.value, 'message': '没有找到相应的用户'}}, status=status.HTTP_400_BAD_REQUEST)
            password = form.cleaned_data['password']
            user = authenticate(
                request, username=username, password=password)
            if user == None or user.is_anonymous:
                return Response({'error': {'code': UserErrorCode.wrong_password.value, 'message': '用户密码错误'}}, status=status.HTTP_400_BAD_REQUEST)
            login(request, user)
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            return Response({'message': '成功登陆', 'data': {'token': token}}, status=status.HTTP_200_OK)
        else:
            # Return an 'invalid login' error message.
            return Response(form.errors, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'])
    def update_user(self, request):
        form = UserProfileForm(request.POST)
        if not form.is_valid():
            return Response({'error': {'code': UserErrorCode.wrong_update_form.value, 'message': '更新用户表单格式不正确，bio字段缺失'}}, status=status.HTTP_400_BAD_REQUEST)
        new_bio = form.cleaned_data['bio']
        if request.FILES['avatar']:
            currentUser.profile.avatar = request.FILES['avatar']
        currentUser = request.user
        currentUser.profile.bio = new_bio
        # password is managed by origianl django, so use the set_password method
        # currentUser.set_password(new_password)
        currentUser.save()
        return Response({'message': '成功更新用户信息', 'data': UserProfileSerializer(currentUser.profile).data}, status=status.HTTP_200_OK)
