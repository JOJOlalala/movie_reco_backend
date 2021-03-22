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
from .serializers import UserSerializer, UserProfileSerializer, UserTaskSerializer
from .models import UserTask
from .interfaces.errorCode.userErrorCode import UserErrorCode


class TaskViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin, IsAdminOrIsSelf):
    queryset = UserTask.objects.all()
    serializer_class = UserTaskSerializer
    permission_classes = [IsAdminOrIsSelf]
    authentication_classes = [JSONWebTokenAuthentication]

    lookup_field = 'taskName'

    @action(detail=False, methods=['get'])
    def get_current_Task(self, request):
        currentUser = request.user
        if currentUser.is_anonymous:
            return Response({'error': {'code': UserErrorCode.unknown_user.value, 'message': '您的身份验证已过期，请重新登陆。'}}, status=status.HTTP_400_BAD_REQUEST)
        userTasks = UserTaskSerializer(
            UserTask.objects.get(user=currentUser)).data
        return Response({
            'message': '成功获取用户任务',
            'data': {
                'userTasks': userTasks
            }}, status=status.HTTP_200_OK)
