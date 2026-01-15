from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    is_referred = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['provider', 'avatar_url', 'banner_url', 'bio', 'xp', 'referral_code', 'is_referred', 'created_at']
        
    def get_is_referred(self, obj):
        return obj.referred_by is not None



class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with profile."""
    
    profile = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'followers_count', 'following_count', 'is_staff', 'is_superuser', 'is_active']
    
    def get_profile(self, obj):
        try:
            return UserProfileSerializer(obj.profile).data
        except:
            return None
        
    def get_followers_count(self, obj):
        return obj.followers.count()
        
    def get_following_count(self, obj):
        return obj.following.count()


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for authentication tokens."""
    
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = UserSerializer(read_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for token refresh request."""
    
    refresh_token = serializers.CharField()


class AdminLoginSerializer(serializers.Serializer):
    """Serializer for admin login."""
    
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(request=self.context.get('request'), username=username, password=password)
            
            if not user:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
            
            if not (user.is_staff or user.is_superuser):
                raise serializers.ValidationError('You do not have permission to access the admin area.')
            
            data['user'] = user
        else:
            raise serializers.ValidationError('Must include "username" and "password".')
            
        return data
