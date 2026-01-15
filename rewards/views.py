from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .models import DailyCheckIn
from .serializers import DailyCheckInSerializer
from authentication.models import UserProfile

class CheckInView(APIView):
    """Handle daily check-in and reward distribution."""
    permission_classes = [IsAuthenticated]
    
    # XP rewards for each streak day
    DAILY_REWARDS = {
        1: 5,
        2: 10,
        3: 15,
        4: 20,
        5: 25,
        6: 30,
        7: 35
    }
    
    def post(self, request):
        """Process a daily check-in."""
        user = request.user
        today = timezone.now().date()
        
        # Check if user already checked in today
        existing_checkin = DailyCheckIn.objects.filter(
            user=user,
            check_in_date=today
        ).first()
        
        if existing_checkin:
            return Response({
                'error': 'Already checked in today',
                'check_in': DailyCheckInSerializer(existing_checkin).data
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the last check-in
        last_checkin = DailyCheckIn.objects.filter(user=user).first()
        
        # Calculate streak day
        if last_checkin:
            yesterday = today - timedelta(days=1)
            
            if last_checkin.check_in_date == yesterday:
                # Consecutive day - increment streak
                streak_day = last_checkin.streak_day + 1
                if streak_day > 7:
                    streak_day = 1  # Reset after 7 days
            else:
                # Missed a day - reset streak
                streak_day = 1
        else:
            # First check-in ever
            streak_day = 1
        
        # Get XP reward for this streak day
        xp_reward = self.DAILY_REWARDS.get(streak_day, 5)
        
        # Create check-in record
        checkin = DailyCheckIn.objects.create(
            user=user,
            streak_day=streak_day,
            xp_earned=xp_reward
        )
        
        # Update user's XP
        profile = user.profile
        profile.xp += xp_reward
        profile.save()
        
        return Response({
            'message': f'Check-in successful! Day {streak_day} streak',
            'check_in': DailyCheckInSerializer(checkin).data,
            'xp_earned': xp_reward,
            'total_xp': profile.xp,
            'streak_day': streak_day
        }, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        """Get user's check-in status and history."""
        user = request.user
        today = timezone.now().date()
        
        # Check today's check-in
        today_checkin = DailyCheckIn.objects.filter(
            user=user,
            check_in_date=today
        ).first()
        
        # Get last check-in for streak calculation
        last_checkin = DailyCheckIn.objects.filter(user=user).first()
        
        # Calculate current streak
        current_streak = 0
        if last_checkin:
            if last_checkin.check_in_date == today or \
               last_checkin.check_in_date == today - timedelta(days=1):
                current_streak = last_checkin.streak_day
        
        # Get recent check-ins (last 7 days)
        recent_checkins = DailyCheckIn.objects.filter(user=user)[:7]
        
        return Response({
            'checked_in_today': today_checkin is not None,
            'current_streak': current_streak,
            'today_checkin': DailyCheckInSerializer(today_checkin).data if today_checkin else None,
            'recent_checkins': DailyCheckInSerializer(recent_checkins, many=True).data,
            'daily_rewards': self.DAILY_REWARDS
        })