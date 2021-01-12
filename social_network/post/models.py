from django.contrib.auth.models import User
from django.db import models


class Post(models.Model):
    data = models.TextField()
    creator = models.ForeignKey(User, blank=False, null=False, on_delete=models.DO_NOTHING, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    fans = models.ManyToManyField(User, related_name='preferences', null=True, blank=True)
