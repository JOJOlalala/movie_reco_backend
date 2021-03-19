from django.db import models

# uesr require
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.db.models.signals import post_save
# Create your models here.


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# class UserProfile(models.Model):
#     # 当生成 user 的时候自动生成 UserProfile，参考之前的 token 生成
#     user = models.OneToOneField(User, related_name="profile",
#                                 on_delete=models.CASCADE)
#     phone_num = models.CharField(max_length=20, unique=True, blank=True)

# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def create_profile(sender, instance=None, created=False, **kwargs):
#     if created:
#         profile, created = UserProfile.objects.get_or_create(user=instance)

#     class ProfileInline(admin.StackInlin):
#         model = UserProfile
#         can_delete = False
#         verbose_name_plural = "profile"

#         class UserAdmin(UserAdmin):
#             inlines = (ProfileInline,)
#             admin.site.unregister(User)
#             admin.site.register(User, UserAdmin)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
