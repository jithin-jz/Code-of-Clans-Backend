from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """
    TAG: Public-facing serializer for user profile data.
    TAG: Explicitly excludes sensitive fields like OAuth tokens.
    """

    # TAG: Computed field to indicate whether this user was referred by someone
    is_referred = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile

        # TAG: Only expose non-sensitive, UI-relevant profile fields
        # TAG: Tokens, provider_id, referred_by are intentionally excluded
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
        # TAG: Boolean derived from presence of a referrer
        return obj.referred_by is not None


class UserSerializer(serializers.ModelSerializer):
    """
    TAG: High-level user serializer used across authenticated APIs.
    TAG: Combines core User fields with derived profile and social metrics.
    """

    # TAG: Profile is injected manually to avoid nested serializer overhead
    profile = serializers.SerializerMethodField()

    # TAG: Social graph metrics (computed, not stored)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User

        # TAG: Includes permission flags for admin-aware frontends
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'profile',
            'followers_count',
            'following_count',
            'is_staff',
            'is_superuser',
            'is_active',
        ]

    def get_profile(self, obj):
        # TAG: Defensive access in case profile was not created (edge cases)
        try:
            return UserProfileSerializer(obj.profile).data
        except:
            return None

    def get_followers_count(self, obj):
        # TAG: Count of users following this user
        return obj.followers.count()

    def get_following_count(self, obj):
        # TAG: Count of users this user follows
        return obj.following.count()


class AuthTokenSerializer(serializers.Serializer):
    """
    TAG: Response serializer for successful authentication.
    TAG: Bundles tokens with user data for frontend bootstrapping.
    """

    # TAG: Short-lived token for authenticated API access
    access_token = serializers.CharField()

    # TAG: Long-lived token used to refresh access tokens
    refresh_token = serializers.CharField()

    # TAG: Embedded user payload to avoid extra /me call on login
    user = UserSerializer(read_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    """
    TAG: Request serializer for refreshing access tokens.
    TAG: Only refresh_token is required; user context is inferred server-side.
    """

    refresh_token = serializers.CharField()


class AdminLoginSerializer(serializers.Serializer):
    """
    TAG: Dedicated serializer for admin-only authentication.
    TAG: Explicitly blocks non-staff users even with valid credentials.
    """

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # TAG: Extract credentials from payload
        username = data.get('username')
        password = data.get('password')

        if username and password:
            # TAG: Delegate credential verification to Django auth backend
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )

            # TAG: Reject invalid credentials
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.'
                )

            # TAG: Enforce admin-only access
            if not (user.is_staff or user.is_superuser):
                raise serializers.ValidationError(
                    'You do not have permission to access the admin area.'
                )

            # TAG: Attach authenticated user to validated data
            data['user'] = user
        else:
            # TAG: Enforce presence of both username and password
            raise serializers.ValidationError(
                'Must include "username" and "password".'
            )

        return data
