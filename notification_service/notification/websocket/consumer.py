import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope.get("user_id")
        
        if not self.user_id:
            await self.close()
            return
            
        self.group_name = f"notifications_{self.user_id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def send_notification(self, event):
        """
        Send notification payload to the WebSocket client.
        Called by group_send in NotificationService._push_to_websocket
        """
        notification = event["notification"]
        await self.send(text_data=json.dumps({
            "type": "notification",
            "data": notification
        }))
