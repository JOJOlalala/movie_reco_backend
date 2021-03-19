from django.urls import include, path
from .views import ArticleViewSet
from .user_api import userRegisterAPIView, userLoginAPIView, userLogoutView
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.

router = DefaultRouter()
router.register('article', ArticleViewSet, basename='article')
# router.register('user', UserViewSet, basename='user')

urlpatterns = [
    path('viewset/', include(router.urls)),
    path('register/', userRegisterAPIView.as_view()),
    path('login/', userLoginAPIView.as_view()),
    path('logout/', userLogoutView.as_view()),
]
