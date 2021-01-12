from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from social_network.post.models import Post
from social_network.post.serializers import PostSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(methods=['post'], detail=False, permission_classes=[])
    def signup(self, request, pk=None):
        return self.create(request)

    @action(methods=['get'], detail=False, permission_classes=[permissions.IsAuthenticated])
    def least_favorite(self, request, pk=None):
        queryset = User.objects.annotate(Count('posts__fans')).annotate(Count('posts')).\
            filter(posts__count__gte=1).filter(posts__fans__count=0)
        queryset = self.filter_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows CRUD operations with Post object.
    Included next actions:
        - like  /posts/<id>/like/ - allows authenticated users to like posts. Once it is called user will be added to
                                    the list of fans for the post.
            202 is returned once like is performed.
            204 is returned if user has already liked a post
        - like  /posts/<id>/unlike/ - allows authenticated users  unlike posts. Once it is called user will be removed
                                      a list of fans for a post
            202 is returned once unlike is performed.
            403 is returned if user has not liked a post and sends unlike request
    Filtering:
        - filtering by creator id
            /posts/?creator=<user_id>

    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_fields = ['creator', 'username']
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['creator']

    @action(methods=['post'], detail=True, permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk)
        user = request.user
        if user in post.fans.all():
            return Response('Post is already liked. No need to do it anymore',
                            status.HTTP_204_NO_CONTENT)
        post.fans.add(request.user)
        return Response('Post is liked', status.HTTP_202_ACCEPTED)

    @action(methods=['post'], detail=True, permission_classes=[permissions.IsAuthenticated])
    def unlike(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk)
        user = request.user
        if user not in post.fans.all():
            return Response(data='Post cant be unliked by the user. It was not liked previously',
                            status=status.HTTP_403_FORBIDDEN)
        post.fans.remove(user)
        return Response(status=status.HTTP_202_ACCEPTED)
