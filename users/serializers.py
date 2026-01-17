from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, UserFollow


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Public-facing serializer for user profile data.
    Explicitly excludes sensitive fields like OAuth tokens.
    """

    # Computed field to indicate whether this user was referred by someone
    is_referred = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile

        # Only expose non-sensitive, UI-relevant profile fields
        # Tokens, provider_id, referred_by are intentionally excluded
        fields = [
            'provider',
            'avatar_url',
            'banner_url',
            'bio',
            'xp',
            'referral_code',
            'is_referred',
            'created_at',
            'github_username',
            'leetcode_username',
        ]

    def get_is_referred(self, obj):
        # Boolean derived from presence of a referrer
        return obj.referred_by is not None


class UserSerializer(serializers.ModelSerializer):
    """
    High-level user serializer used across authenticated APIs.
    Combines core User fields with derived profile and social metrics.
    """

    # Profile is injected manually to avoid nested serializer overhead
    profile = serializers.SerializerMethodField()

    # Social graph metrics (computed, not stored)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User

        # Includes permission flags for admin-aware frontends
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'profile',          # Nested profile data (avatar, bio, etc.)
            'followers_count',  # Social proof metric
            'following_count',  # Social proof metric
            'is_staff',         # For Access Control (e.g. show Admin Link)
            'is_superuser',     # For Access Control
            'is_active',        # Status check
        ]

    def get_profile(self, obj):
        # Defensive access in case profile was not created (edge cases)
        try:
            return UserProfileSerializer(obj.profile).data
        except:
            return None

    def get_followers_count(self, obj):
        # Count of users following this user
        return obj.followers.count()

    def get_following_count(self, obj):
        # Count of users this user follows
        return obj.following.count()
