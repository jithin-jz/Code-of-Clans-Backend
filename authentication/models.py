from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile to store OAuth provider information."""
    
    PROVIDER_CHOICES = [
        ('github', 'GitHub'),
        ('google', 'Google'),
        ('discord', 'Discord'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_id = models.CharField(max_length=255)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    banner_url = models.URLField(max_length=500, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)

    # Social Accounts
    github_username = models.CharField(max_length=100, blank=True, null=True)
    leetcode_username = models.CharField(max_length=100, blank=True, null=True)
    
    # Referral System
    xp = models.IntegerField(default=0)
    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['provider', 'provider_id']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            import random
            import string
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not UserProfile.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)
    
    def toggle_block(self):
        """Toggle the active status of the associated user."""
        self.user.is_active = not self.user.is_active
        self.user.save()
        return self.user.is_active

    def __str__(self):
        return f"{self.user.username} ({self.provider})"

class UserFollow(models.Model):
    """Model to store follower/following relationships."""
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', 'following']),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        UserProfile.objects.create(
            user=instance,
            provider='local',
            provider_id=f"local_{instance.id}",
            bio="Administrator" if instance.is_superuser else "User"
        )
