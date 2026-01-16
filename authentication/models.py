from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile to store OAuth provider information."""

    # TAG: Supported OAuth providers for authentication
    PROVIDER_CHOICES = [
        ('github', 'GitHub'),
        ('google', 'Google'),
        ('discord', 'Discord'),
    ]

    # TAG: One-to-one link ensures exactly one profile per user
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # TAG: OAuth provider name (github/google/discord/local)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)

    # TAG: Unique user ID returned by the OAuth provider
    provider_id = models.CharField(max_length=255)

    # TAG: Public profile visuals
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    banner_url = models.URLField(max_length=500, blank=True, null=True)

    # TAG: Short user bio shown on profile
    bio = models.TextField(max_length=500, blank=True, null=True)

    # TAG: OAuth tokens for API access (sensitive data)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)

    # TAG: Linked social accounts (not used for authentication)
    github_username = models.CharField(max_length=100, blank=True, null=True)
    leetcode_username = models.CharField(max_length=100, blank=True, null=True)

    # TAG: Referral and gamification system
    xp = models.IntegerField(default=0)
    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)

    # TAG: Self-referencing relationship for referrals
    referred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals'
    )

    # TAG: Audit timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # TAG: Prevent same OAuth account from being reused
        unique_together = ['provider', 'provider_id']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def save(self, *args, **kwargs):
        # TAG: Auto-generate unique referral code if missing
        if not self.referral_code:
            import random
            import string
            while True:
                code = ''.join(
                    random.choices(string.ascii_uppercase + string.digits, k=8)
                )
                if not UserProfile.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)

    def toggle_block(self):
        """Toggle the active status of the associated user."""
        # TAG: Soft block by disabling login access
        self.user.is_active = not self.user.is_active
        self.user.save()
        return self.user.is_active

    def __str__(self):
        # TAG: Human-readable identifier for admin/debugging
        return f"{self.user.username} ({self.provider})"


class UserFollow(models.Model):
    """Model to store follower/following relationships."""

    # TAG: User who initiates the follow
    follower = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE
    )

    # TAG: User being followed
    following = models.ForeignKey(
        User,
        related_name='followers',
        on_delete=models.CASCADE
    )

    # TAG: Timestamp of follow action
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # TAG: Prevent duplicate follow relationships
        unique_together = ['follower', 'following']

        # TAG: Optimize follower/following queries
        indexes = [
            models.Index(fields=['follower', 'following']),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # TAG: Automatically create profile when a user is created
    if created and not hasattr(instance, 'profile'):
        UserProfile.objects.create(
            user=instance,
            provider='local',
            provider_id=f"local_{instance.id}",
            bio="Administrator" if instance.is_superuser else "User"
        )
