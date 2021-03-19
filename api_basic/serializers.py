from rest_framework import serializers
from .models import Article
from django.contrib.auth.models import User


# class UserSerializer(serializers.ModelSerializer):
#     snippets = serializers.PrimaryKeyRelatedField(
#         many=True, queryset=Snippet.objects.all())

#     class Meta:
#         model = User
#         fields = ['id', 'username', 'snippets']


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        # manully add properties
        # fields = ['id', 'title', 'author']
        fields = '__all__'
