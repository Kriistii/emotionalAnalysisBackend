from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
import uuid
from .services import chatbot, video, audio
from .models import ChatSession, ChatSessionMessage, Employee
import filetype
import datetime

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        employee_id = self.scope['url_route']['kwargs']['employee_id']
        session_id = uuid.uuid4()
        self.scope["session"]['session_id'] = session_id
    
        employee = Employee.objects.get(id = employee_id)
        session = ChatSession.objects.create(id = session_id, employee = employee, date = datetime.date.today())
        session.save()
        await self.accept()

    def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        employee_id = self.scope['url_route']['kwargs']['employee_id']
        session_id = self.scope["session"]
        name = uuid.uuid4()
        try:
            if text_data:
                message = json.loads(text_data)
                answer = chatbot.compute_answer(session_id, message['data'], employee_id)
                createChatSessionMessage(session_id, message, answer, None, None)
                await self.send(json.dumps({"answer_chatbot": answer, "question": message['data'], "type": 'text'}))
            if bytes_data:
                kind = filetype.guess(bytes_data)
                if kind.extension == 'wav':
                    audio_file = bytes_data
                    audio_path = audio.save_audio(audio_file, name) #add path to return of save audio
                    text = audio.speech_to_text(name)
                    answer = chatbot.compute_answer(session_id, text, employee_id)
                    createChatSessionMessage(session_id, text, answer, audio_path, None)
                    await self.send(json.dumps({"answer_chatbot": answer, "question": text, "type": 'media'}))
                elif kind.extension == 'mkv':
                    video_file = bytes_data
                    video_path = video.save_video(session_id, video_file, name)#add path to return of save video
                    #video.analyze_video(name)
                    audio_path = audio.video_to_audio(name)
                    text = audio.speech_to_text(name)
                    answer = chatbot.compute_answer(session_id, text, employee_id)
                    createChatSessionMessage(session_id, text, answer, audio_path, video_path)
                    await self.send(json.dumps({"answer_chatbot": answer, "question": text, "type": 'media'}))
        except Exception as e:
            print(e)


    def createChatSessionMessage(session_id, text, answer, audio, video):
        session = ChatSession.objects.get(id = session_id)
        message = ChatSessionMessage.objects.create(session = session, text = text,
         chatbot_answer = answer, date = datetime.date.today(), audio_url = audio, video_url = video)
         #add null true to audio and video url
        message.save()


