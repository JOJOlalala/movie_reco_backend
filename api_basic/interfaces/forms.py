from django import forms
from django.contrib.auth.models import User
from ..models import Profile


class LoginForm(forms.Form):

    # if needed, set required=False
    username = forms.CharField()
    password = forms.CharField()


# use model from to inherit other model's properties
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username',)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('url', 'location', 'company')
