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
        username = self.scope["user"].username

        # Save to DB
        await self.save_message(message)

        # Broadcast
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username']
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
        return [{'username': m.user.username, 'message': m.content} for m in reversed(messages)]