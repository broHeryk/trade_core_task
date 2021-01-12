from django.contrib.auth.models import User
from rest_framework import serializers

from social_network.post.models import Post
from social_network.post.utils import fetch_name_data, verify_email


class UserSerializer(serializers.HyperlinkedModelSerializer):
    password = serializers.CharField(max_length=128, write_only=True)

    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'first_name', 'last_name', 'password', 'id']

    def validate_email(self, email):
        verify_email(email)
        return email

    def to_internal_value(self, data):
        super().to_internal_value(data)
        name_data = fetch_name_data(data.get('email'))
        if name_data:
            data = data.copy()
        data.update(name_data)
        return data

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class PostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Post
        fields = ['data', 'creator', 'created_at', 'fans', 'url']
