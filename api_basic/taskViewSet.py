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

# scrapy crawler
from .interfaces.crawler.run import run_crawl


def check_user_and_task(request, id):
    currentUser = request.user
    if currentUser.is_anonymous:
        return False, Response({'error': {'code': UserErrorCode.unknown_user.value, 'message': '您的身份验证已过期，请重新登陆。'}}, status=status.HTTP_400_BAD_REQUEST)
    try:
        currentTask = UserTask.objects.get(id=id)
    except ObjectDoesNotExist:
        return False, Response({'error': {'code': TaskErrorCode.unknown_task.value, 'message': '不存在的任务。'}}, status=status.HTTP_400_BAD_REQUEST)
    if currentTask.user.id != currentUser.id:
        return False, Response({'error': {'code': TaskErrorCode.permission_deny.value, 'message': '你没有权限访问该任务'}}, status=status.HTTP_400_BAD_REQUEST)
    return True, [currentUser, currentTask]


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
            base_path = settings.MEDIA_ROOT + '/tasks/{0}/{1}/photo_capture'.format(
                currentUser.username, data['taskName'])
            if Path(base_path).is_dir():
                data['isProcessed'] = True
            else:
                data['isProcessed'] = False
            resData.append(data)
        return Response({
            'message': '成功获取用户任务',
            'data': {
                'userTasks': resData
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

    @action(detail=True, methods=['post'])
    def extract_actors(self, request, id):
        state, res = check_user_and_task(request, id)
        if state == False:
            return res
        currentUser = res[0]
        currentTask = res[1]
        save_path = settings.MEDIA_ROOT + '/tasks/{0}/{1}'.format(
            currentUser.username, currentTask.taskName)
        maximum_index = request.POST['maximumIndex']
        maximum_frame_per_index = request.POST['maximumFramePerIndex']
        maximum_num = request.POST['maximumNum']
        # use .encode when there are Chinese Characters in your path
        CatchPICFromVideo(str(currentTask.originalVideo), int(maximum_index), int(maximum_frame_per_index),
                          int(maximum_num), save_path)
        return Response({
            'message': '人脸提取成功',
            'data': {

            }}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def get_task_actors(self, request, id):
        state, res = check_user_and_task(request, id)
        if state == False:
            return res
        currentUser, currentTask = res
        base_path = 'media/tasks/{0}/{1}'.format(
            currentUser.username, currentTask.taskName)
        save_path = base_path+'/photo_capture'
        if not Path(save_path).is_dir():
            # 还未进行人脸提取和分类
            return Response({'error': {'code': TaskErrorCode.unprocessed_video.value, 'message': '该视频还未进行预处理。'}}, status=status.HTTP_200_OK)

        dirs = os.listdir(save_path)
        # 这里需要提取图片的id进行排序，否则会出现:1.jpg, 10.jpg, 2.jpg的情况
        dirs.sort(key=lambda x: int(x[3:]))
        img_list = []
        if request.GET.get('index') is not None:
            res_index = request.GET.get('index')
            dir_found_flag = False
            for dir in dirs:
                if str(dir) == 'id_'+res_index:
                    dir_found_flag = True
                    key_path = save_path+'/'+str(dir)
                    imgs = Path(key_path).rglob('*.jpg')
                    for img in imgs:
                        img_list.append(str(img))
            if dir_found_flag == False:
                return Response({'error': {'code': TaskErrorCode.unexist_index.value, 'message': '没有该索引目录。'}}, status=status.HTTP_400_BAD_REQUEST)
        else:
            for dir in dirs:
                key_path = save_path+'/'+str(dir)+'/key_frame/'
                imgs = os.listdir(key_path)
                for img in imgs:
                    img_list.append(key_path+img)
        if request.GET.get('method') is None:
            return Response({'error': {'code': TaskErrorCode.lack_of_params.value, 'message': '缺少方法参数method'}}, status=status.HTTP_400_BAD_REQUEST)
        method = request.GET.get('method')
        if method == '0':
            # 只返回图片路径，不进行演员搜索
            # 对人物进行检索
            return Response({
                'message': '人脸提取成功',
                'data': {
                    'imgList': img_list
                }}, status=status.HTTP_200_OK)
        else:
            data_list = []
            if method == '1':
                # 只打开现有的actors.json文件返回信息，如果没有返回空数组
                if Path(base_path+'/actors.json').is_file():
                    with open(base_path+'/actors.json', 'r', encoding='utf-8') as file1:
                        data_list = json.load(file1)
            elif method == '2':
                # 重新进行检索（发送请求）
                for img in img_list:
                    data_list.append(huawei_search_actor(img))
                with open(base_path+'/actors.json', 'w', encoding='utf-8') as file1:
                    file1.write(json.dumps(
                        data_list, indent=2, ensure_ascii=False))
                if Path(base_path+'/actor_list.json').exists():
                    Path(base_path+'/actor_list.json').unlink()
            return Response({
                'message': '人脸提取成功',
                'data': {
                    'imgList': data_list
                }}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def delete_video(self, request, id):
        state, res = check_user_and_task(request, id)
        if state == False:
            return res
        currentUser = res[0]
        currentTask = res[1]
        # delete relative files
        base_path = settings.MEDIA_ROOT + '/tasks/{0}/{1}'.format(
            currentUser.username, currentTask.taskName)
        currentTask.delete()
        shutil.rmtree(base_path)
        return Response({
            'message': '视频删除成功',
            'data': {

            }}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def key_frame_shuffle(self, request, id):
        state, res = check_user_and_task(request, id)
        if state == False:
            return res
        currentUser, currentTask = res
        # 移动相关文件
        if request.GET.get('imgPath') is None:
            return Response({'error': {'code': TaskErrorCode.lack_of_params.value, 'message': '缺少方法参数imgPath'}}, status=status.HTTP_400_BAD_REQUEST)
        img_path = request.GET.get('imgPath')
        # save_path = '/'.join(img_path.split('\\\\')[:-1])
        if img_path.split('\\')[-2] == "key_frame":
            None
        else:
            key_frame_dir = '/'.join(img_path.split('\\')[1:-1])
            old_path = settings.MEDIA_ROOT + '/' + key_frame_dir
            img_path = settings.MEDIA_ROOT + '/' + \
                '/'.join(img_path.split('\\')[1:])
            save_path = old_path + '/key_frame/'
            old_imgs = os.listdir(save_path)
            for old_img in old_imgs:
                shutil.move(save_path+str(old_img), old_path)
            shutil.move(img_path, save_path)
        return Response({
            'message': '移动成功',
            'data': {

            }}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def crawl(self, request, id):
        state, res = check_user_and_task(request, id)
        if state == False:
            return res
        currentUser, currentTask = res
        base_path = 'media/tasks/{0}/{1}'.format(
            currentUser.username, currentTask.taskName)
        if Path(base_path+'/actors.json').exists():
            run_crawl(base_path)
        else:
            return Response({'error': {'code': TaskErrorCode.lack_of_params.value, 'message': '任务尚未及进行演员提取'}}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': '爬取完成'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def get_actors(self, request, id):
        state, res = check_user_and_task(request, id)
        if state == False:
            return res
        currentUser, currentTask = res
        base_path = 'media/tasks/{0}/{1}'.format(
            currentUser.username, currentTask.taskName)

        if Path(base_path+"/actor_list.json").exists():
            with open(base_path+"/actor_list.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            return Response({'error': {'code': TaskErrorCode.lack_of_params.value, 'message': '任务尚未及进行演员爬取,actor_list缺失'}, 'data': []}, status=status.HTTP_200_OK)

        return Response({
            'message': '爬取完成', 'data': data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def get_movies(self, request, id):
        state, res = check_user_and_task(request, id)
        if state == False:
            return res
        currentUser, currentTask = res
        base_path = 'media/tasks/{0}/{1}'.format(
            currentUser.username, currentTask.taskName)
        if not Path(base_path+'/movies').exists():
            return Response({'error': {'code': TaskErrorCode.lack_of_params.value, 'message': '任务尚未及进行演员提取。'}}, status=status.HTTP_400_BAD_REQUEST)

        if request.GET.get('actor') is not None:
            actor = request.GET.get('actor')
            if Path(base_path+"/movies/{}.json".format(actor)).exists():
                with open(base_path+"/movies/{}.json".format(actor), "r", encoding="utf-8") as f:
                    data = json.load(f)
        else:
            return Response({'error': {'code': TaskErrorCode.lack_of_params.value, 'message': '需要演员名称。'}}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': '爬取完成', 'data': data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def get_intersections(self, request, id):
        state, res = check_user_and_task(request, id)
        if state == False:
            return res
        currentUser, currentTask = res
        base_path = 'media/tasks/{0}/{1}'.format(
            currentUser.username, currentTask.taskName)
        if not Path(base_path+'/movies').exists():
            return Response({'error': {'code': TaskErrorCode.lack_of_params.value, 'message': '任务尚未及进行演员提取。'}}, status=status.HTTP_400_BAD_REQUEST)

        if Path(base_path+"/actor_list.json").exists():
            class movieClass:
                def __init__(self, title, link, date, rating):
                    self.title = title
                    self.link = link
                    self.date = date
                    self.rating = rating

                def __hash__(self):
                    return hash(self.title)

                def __eq__(self, other):
                    if isinstance(other, self.__class__):
                        return hash(self.title) == hash(other.title)
                    else:
                        return False

            with open(base_path+"/actor_list.json", "r", encoding="utf-8") as f:
                actors = json.load(f)
            if len(actors) > 0:
                file_path = base_path + \
                    "/movies/{}.json".format(actors[0]['name'])
                with open(file_path, "r", encoding="utf-8") as f:
                    movies = json.load(f)
                    res_set = set()
                    for movie in movies:
                        movie_class = movieClass(
                            movie['title'], movie['link'], movie['date'], movie['rating'])
                        res_set.add(movie_class)
            for i in range(1, len(actors)):
                file_path = base_path + \
                    "/movies/{}.json".format(actors[i]['name'])
                with open(file_path, "r", encoding="utf-8") as f:
                    movies = json.load(f)
                    movie_set = set()
                    for movie in movies:
                        movie_class = movieClass(
                            movie['title'], movie['link'], movie['date'], movie['rating'])
                        movie_set.add(movie_class)
                    res_set = res_set.intersection(movie_set)
            res_list = list(res_set)
            res_list = map(lambda obj: obj.__dict__, res_list)
        else:
            return Response({'error': {'code': TaskErrorCode.lack_of_params.value, 'message': '任务尚未及进行演员爬取,actor_list缺失'}, 'data': []}, status=status.HTTP_200_OK)

        return Response({
            'message': '交集提取完成', 'data': res_list}, status=status.HTTP_200_OK)
