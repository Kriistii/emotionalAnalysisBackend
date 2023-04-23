from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
import uuid
from .services import chatbot, video, audio, text_service, chat, session
from .models import Employee
import filetype



class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        employee_id = self.scope['url_route']['kwargs']['employee_id']
        session_id = uuid.uuid4()
        self.scope["session"]['session_id'] = session_id
        await session.createSession(session_id, employee_id)
        await self.accept()

    async def disconnect(self, close_code):
        session_value = self.scope["session"]
        session_id = session_value['session_id']
        employee_id = self.scope['url_route']['kwargs']['employee_id']
        await session.completeSession(session_id, employee_id)
        pass

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        employee_id = self.scope['url_route']['kwargs']['employee_id']
        session_value = self.scope["session"]
        session_id = session_value['session_id']
        name = uuid.uuid4()
        text = None
        answer = None
        response = None
        video_path = None
        audio_path = None
        try:
            if bytes_data:
                video_file = bytes_data
                video_path = video.save_video(session_id, video_file, name)
                audio_path = audio.video_to_audio(session_id, name)
                text = audio.speech_to_text(session_id, name)
            await session.createSession(session_id, text, answer, audio_path, video_path)
            await self.send(response)

        except Exception as e:
            print(e)

