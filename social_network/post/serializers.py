import threading

from django.contrib.auth.models import User
from rest_framework import serializers

from social_network.post.models import Post
from social_network.post.utils import fetch_name_data, verify_email, populate_clearbit_user_data_async


class UserSerializer(serializers.HyperlinkedModelSerializer):
    password = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'first_name', 'last_name', 'password', 'id']

    def validate_email(self, email):
        verify_email(email)
        return email

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        populate_clearbit_user_data_async(user.pk, user.email)
        return user


class PostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Post
        fields = ['data', 'creator', 'created_at', 'fans', 'url']
