from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
import uuid
from .services import chatbot, video, audio
import filetype

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        employee_id = self.scope['url_route']['kwargs']['employee_id']
        self.scope["session"]['session_id'] = uuid.uuid4()
        #Create the session
        await self.accept()

    def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        employee_id = self.scope['url_route']['kwargs']['employee_id']
        session = self.scope["session"]
        name = uuid.uuid4()
        try:
            if text_data:
                message = json.loads(text_data)
                answer = chatbot.compute_answer(session, message['data'], employee_id)
                await self.send(json.dumps({"answer_chatbot": answer, "question": message['data'], "type": 'text'}))
            if bytes_data:
                kind = filetype.guess(bytes_data)
                if kind.extension == 'wav':
                    audio_file = bytes_data
                    audio.save_audio(audio_file, name)
                    text = audio.speech_to_text(name)
                    answer = chatbot.compute_answer(session, text, employee_id)
                    await self.send(json.dumps({"answer_chatbot": answer, "question": text, "type": 'media'}))
                elif kind.extension == 'mkv':
                    video_file = bytes_data
                    video.save_video(video_file, name)
                    #video.analyze_video(name)
                    audio.video_to_audio(name)
                    text = audio.speech_to_text(name)
                    answer = chatbot.compute_answer(session, text, employee_id)
                    await self.send(json.dumps({"answer_chatbot": answer, "question": text, "type": 'media'}))
        except Exception as e:
            print(e)


