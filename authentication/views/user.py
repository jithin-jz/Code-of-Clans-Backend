from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import UserProfile
from ..serializers import UserSerializer, RefreshTokenSerializer
from ..utils import (
    generate_access_token,
    decode_token,
)

class CurrentUserView(APIView):
    """Get the currently authenticated user."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class RefreshTokenView(APIView):
    """Refresh the access token using a refresh token."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        token = serializer.validated_data['refresh_token']
        payload = decode_token(token)
        
        if not payload:
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if payload.get('type') != 'refresh':
            return Response(
                {'error': 'Invalid token type'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            user = User.objects.get(id=payload['user_id'])
        except User.DoesNotExist:
             return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not user.is_active:
             return Response(
                {'error': 'User account is disabled.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_access_token = generate_access_token(user)
        
        return Response({
            'access_token': new_access_token,
            'user': UserSerializer(user).data
        })


class LogoutView(APIView):
    """Logout the user (client should delete tokens)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # In a stateless JWT system, logout is handled client-side
        # We just return success here
        return Response({'message': 'Successfully logged out'})


class DeleteAccountView(APIView):
    """View to delete the user account."""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        user = request.user
        user.delete()
        return Response({'message': 'Account deleted successfully'})


class RedeemReferralView(APIView):
    """View to redeem a referral code."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response({'error': 'Referral code is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if profile.referred_by:
            return Response({'error': 'You have already redeemed a referral code'}, status=status.HTTP_400_BAD_REQUEST)
            
        if profile.referral_code == code:
            return Response({'error': 'Cannot redeem your own referral code'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            referrer_profile = UserProfile.objects.get(referral_code=code)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Invalid referral code'}, status=status.HTTP_404_NOT_FOUND)
            
        # Update user profile
        profile.referred_by = referrer_profile.user
        profile.xp += 100  # Award 100 XP
        profile.save()
        
        return Response({
            'message': 'Referral code redeemed successfully',
            'xp_awarded': 100,
            'new_total_xp': profile.xp
        })
