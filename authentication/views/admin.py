from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import UserSerializer, AdminLoginSerializer
from ..utils import generate_tokens

class AdminLoginView(APIView):
    """Admin login view."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        tokens = generate_tokens(user)
        
        return Response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user': UserSerializer(user).data
        })


class UserListView(APIView):
    """View to list all users for admin."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
             return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        users = User.objects.all().order_by('-date_joined')
        return Response(UserSerializer(users, many=True).data)


class UserBlockToggleView(APIView):
    """View to toggle user active status."""
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        if not (request.user.is_staff or request.user.is_superuser):
             return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
             return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if user == request.user:
             return Response({'error': 'Cannot block yourself'}, status=status.HTTP_400_BAD_REQUEST)

        # Toggle status directly on user model
        user.is_active = not user.is_active
        user.save()
        
        return Response({
            'message': f"User {'unblocked' if user.is_active else 'blocked'} successfully",
            'is_active': user.is_active
        })
