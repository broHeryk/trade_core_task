from rest_framework import routers

from social_network.post import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'posts', views.PostViewSet, basename='post')
