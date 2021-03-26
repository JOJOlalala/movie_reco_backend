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
from django.core.files.base import ContentFile
from django.db import IntegrityError

from .interfaces.forms import LoginForm, UserForm, UserTaskForm
from .permissions import IsAdminOrOwnTask
from .serializers import UserSerializer, UserProfileSerializer, UserTaskSerializer
from .models import UserTask
from .interfaces.errorCode.userErrorCode import UserErrorCode
from .interfaces.errorCode.taskErrorCode import TaskErrorCode
from .interfaces.taskAdmin.photo_process import processed_video, huawei_search_actor

# movie reco
from django.conf import settings
from .interfaces.taskAdmin.videoReco import CatchPICFromVideo
from .interfaces.taskAdmin.face_classify import cv_imread
import json
from pathlib import Path
import os
import random
import cv2
import shutil


class TaskViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, IsAdminOrOwnTask):
    queryset = UserTask.objects.all()
    serializer_class = UserTaskSerializer
    permission_classes = [IsAdminOrOwnTask, IsAuthenticated]
    authentication_classes = [JSONWebTokenAuthentication]

    # use default pk
    lookup_field = 'id'

    @action(detail=False, methods=['get'])
    def get_current_task(self, request):
        currentUser = request.user
        if currentUser.is_anonymous:
            return Response({'error': {'code': UserErrorCode.unknown_user.value, 'message': '您的身份验证已过期，请重新登陆。'}}, status=status.HTTP_400_BAD_REQUEST)
        tasks_query = UserTask.objects.filter(
            user=currentUser.id)
        tasks = list(tasks_query)
        if len(tasks) == 0:
            return Response({'error': {'code': TaskErrorCode.empty_task.value, 'message': '您还未创建任何任务。'}})
        resData = []
        for task in tasks:
            data = UserTaskSerializer(task).data
            print(data)
            basePath = settings.MEDIA_ROOT + '/tasks/{0}/{1}/photo_capture'.format(
                currentUser.username, data['taskName'])
            if Path(basePath).is_dir():
                data['isProcessed'] = True
            else:
                data['isProcessed'] = False
            resData.append(data)
        return Response({
            'message': '成功获取用户任务',
            'data': {
                'userTasks': resData
            }}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def extract_actors(self, request, id):
        try:
            currentTask = UserTask.objects.get(id=id)
        except ObjectDoesNotExist:
            return Response({'error': {'code': TaskErrorCode.unknown_task.value, 'message': '不存在的任务。'}})
        # start actor reco
        currentUser = request.user
        if currentUser.is_anonymous:
            return Response({'error': {'code': UserErrorCode.unknown_user.value, 'message': '您的身份验证已过期，请重新登陆。'}}, status=status.HTTP_400_BAD_REQUEST)
        if currentTask.user.id != currentUser.id:
            return Response({'error': {'code': TaskErrorCode.permission_deny.value, 'message': '你没有权限访问该任务'}}, status=status.HTTP_400_BAD_REQUEST)
        save_path = settings.MEDIA_ROOT + '/tasks/{0}/{1}'.format(
            currentUser.username, currentTask.taskName)
        photo_num = request.POST['photoNum']
        photo_index = request.POST['photoIndex']
        # use .encode when there are Chinese Characters in your path
        CatchPICFromVideo(str(currentTask.originalVideo), int(photo_index),
                          int(photo_num), save_path)
        return Response({
            'message': '人脸提取成功',
            'data': {

            }}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def get_task_actors(self, request, id):
        try:
            currentTask = UserTask.objects.get(id=id)
        except ObjectDoesNotExist:
            return Response({'error': {'code': TaskErrorCode.unknown_task.value, 'message': '不存在的任务。'}})
        # start actor reco
        currentUser = request.user
        if currentUser.is_anonymous:
            return Response({'error': {'code': UserErrorCode.unknown_user.value, 'message': '您的身份验证已过期，请重新登陆。'}}, status=status.HTTP_400_BAD_REQUEST)
        if currentTask.user.id != currentUser.id:
            return Response({'error': {'code': TaskErrorCode.permission_deny.value, 'message': '你没有权限访问该任务'}}, status=status.HTTP_400_BAD_REQUEST)
        basePath = settings.MEDIA_ROOT + '/tasks/{0}/{1}'.format(
            currentUser.username, currentTask.taskName)
        save_path = basePath+'/photo_capture'
        if not Path(save_path).is_dir():
            # 还未进行人脸提取和分类
            return Response({'error': {'code': TaskErrorCode.unprocessed_video.value, 'message': '该视频还未进行预处理。'}}, status=status.HTTP_400_BAD_REQUEST)
        files = os.listdir(save_path)
        img_list = []
        for file in files:
            img_path = save_path+'/'+str(file)
            img_list.append(img_path)
        # 对人物进行检索
        data_list = []
        for img in img_list:
            print(img)
            data_list.append(huawei_search_actor(img))
        with open(basePath+'/actors.json', 'w', encoding='utf-8') as file1:
            file1.write(json.dumps(data_list, indent=2, ensure_ascii=False))
        return Response({
            'message': '人脸提取成功',
            'data': {
                'imgList': data_list
            }}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def upload_video(self, request):
        currentUser = request.user
        if currentUser.is_anonymous:
            return Response({'error': {'code': UserErrorCode.unknown_user.value, 'message': '您的身份验证已过期，请重新登陆。'}}, status=status.HTTP_400_BAD_REQUEST)

        if request.POST.get('taskName') is not None:
            task_name = request.POST.get('taskName')
            if task_name == '':
                return Response({'error': {'code': TaskErrorCode.wrong_update_form.value, 'message': '任务名不能为空'}}, status=status.HTTP_400_BAD_REQUEST)
            try:
                new_task = UserTask.objects.create(
                    user=currentUser, taskName=request.POST.get('taskName'))
            except IntegrityError as e:
                if 'UNIQUE constraint' in str(e):
                    return Response({'error': {'code': TaskErrorCode.task_already_exist.value, 'message': '已经存在相同名称的任务，请重新命名。'}}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'error': {'code': TaskErrorCode.task_already_exist.value, 'message': '神秘错误。'}}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': {'code': TaskErrorCode.wrong_update_form.value, 'message': '任务名缺失。'}}, status=status.HTTP_400_BAD_REQUEST)
        if request.FILES.get('originalVideo') is not None:
            file_content = ContentFile(request.FILES['originalVideo'].read())
            new_task.originalVideo.save(
                request.FILES['originalVideo'].name, file_content)
            return Response({
                'message': '视频上传成功',
                'data': {

                }}, status=status.HTTP_200_OK)
        else:
            return Response({'error': {'code': TaskErrorCode.wrong_update_form.value, 'message': '上传视频表单格式不正确，视频文件缺失。'}}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def delete_video(self, request, id):
        currentUser = request.user
        if currentUser.is_anonymous:
            return Response({'error': {'code': UserErrorCode.unknown_user.value, 'message': '您的身份验证已过期，请重新登陆。'}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            currentTask = UserTask.objects.get(id=id)
        except ObjectDoesNotExist:
            return Response({'error': {'code': TaskErrorCode.unknown_task.value, 'message': '不存在的任务。'}}, status=status.HTTP_400_BAD_REQUEST)
        if currentTask.user.id != currentUser.id:
            return Response({'error': {'code': TaskErrorCode.permission_deny.value, 'message': '你没有权限访问该任务'}}, status=status.HTTP_400_BAD_REQUEST)
        # 删除相关文件
        basePath = settings.MEDIA_ROOT + '/tasks/{0}/{1}'.format(
            currentUser.username, currentTask.taskName)
        currentTask.delete()
        shutil.rmtree(basePath)
        return Response({
            'message': '视频删除成功',
            'data': {

            }}, status=status.HTTP_200_OK)
