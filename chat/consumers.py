import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    connected_channels = set()

    async def connect(self):
        print(f"WS Attempt Connect: {self.channel_name}")
        self.room_group_name = "global_chat"
        
        # Verify user is authenticated
        user = self.scope.get("user")
        print(f"WS User: {user}")
        if not user or user.is_anonymous:
            print("WS Rejected: Anonymous")
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        # Add to connected list and broadcast update
        ChatConsumer.connected_channels.add(self.channel_name)
        await self.broadcast_user_count()

        await self.accept()
        print("WS Accepted")

        # Send last 50 messages
        messages = await self.get_last_50_messages()
        for msg in messages:
            await self.send(text_data=json.dumps(msg))

    async def disconnect(self, close_code):
        print(f"WS Disconnect: {self.channel_name}")
        # Remove from connected list and broadcast update
        ChatConsumer.connected_channels.discard(self.channel_name)
        await self.broadcast_user_count()

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        print(f"WS Receive: {text_data}")
        data = json.loads(text_data)
        message = data['message']
        user = self.scope["user"]
        username = user.username
        
        # Get user data safely
        user_data = await self.get_user_data(user)

        # Save to DB
        await self.save_message(message)

        # Broadcast
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'user_id': user_data['user_id'],
                'avatar_url': user_data['avatar_url']
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'user_id': event.get('user_id'),
            'avatar_url': event.get('avatar_url')
        }))
    
    async def user_count(self, event):
        # print(f"WS User Count: {event['count']}")
        await self.send(text_data=json.dumps({
            'type': 'user_count',
            'count': event['count']
        }))

    async def broadcast_user_count(self):
        count = len(ChatConsumer.connected_channels)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_count',
                'count': count
            }
        )

    @database_sync_to_async
    def save_message(self, message):
        return Message.objects.create(user=self.scope["user"], content=message)

    @database_sync_to_async
    def get_last_50_messages(self):
        messages = Message.objects.all().order_by('-timestamp')[:50]
        result = []
        for m in reversed(messages):
            avatar_url = None
            try:
                if hasattr(m.user, 'profile'):
                    avatar_url = m.user.profile.avatar_url
            except Exception:
                pass
            
            result.append({
                'username': m.user.username,
                'message': m.content,
                'user_id': m.user.id,
                'avatar_url': avatar_url
            })
        return result

    @database_sync_to_async
    def get_user_data(self, user):
        avatar_url = None
        try:
            if hasattr(user, 'profile'):
                avatar_url = user.profile.avatar_url
        except Exception:
            pass
            
        return {
            'user_id': user.id,
            'avatar_url': avatar_url
        }