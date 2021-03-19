from django.contrib import admin
from .models import Article

# user require
# import as alias to prevent confusing
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile
from django.contrib.auth.models import User
# Register your models here.

admin.site.register(Article)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "profile"


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
