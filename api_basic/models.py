from django.db import models

# uesr require
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.contrib import admin
from django.db.models.signals import post_save
from django.conf import settings
# Create your models here.


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


def image_upload_path(instance, filename):
    return settings.MEDIA_ROOT + '/userProfile/{0}/{1}'.format(instance.user.username, filename)


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(
        max_length=255, blank=True, upload_to=image_upload_path)
