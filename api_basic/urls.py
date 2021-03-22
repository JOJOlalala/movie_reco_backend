from django.urls import include, path
from .views import ArticleViewSet
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import verify_jwt_token
from .userViewSet import UserViewSet
from .taskViewSet import TaskViewSet

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.

router = DefaultRouter()
router.register('article', ArticleViewSet, basename='article')
router.register('user', UserViewSet, basename='user')
router.register('task', TaskViewSet, basename='task')
# router.register('user', UserViewSet, basename='user')

urlpatterns = [
    path('api/', include(router.urls)),
    # 200 response if valid, otherwise 400 bad request
    path('api/api-token-verify/', verify_jwt_token)
]
