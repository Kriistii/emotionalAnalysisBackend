from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
import uuid
from .services import chatbot, video, audio, text_service, chat
from .models import ChatSession, ChatSessionMessage, Employee
import filetype

from asgiref.sync import sync_to_async


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        employee_id = self.scope['url_route']['kwargs']['employee_id']
        session_id = uuid.uuid4()
        self.scope["session"]['session_id'] = session_id
        await chat.createChatSession(session_id, employee_id)
        await self.accept()

    async def disconnect(self, close_code):
        session = self.scope["session"]
        chat_session_id = session['session_id']
        text_analysis_results = await text_service.mergeAndAnalyzeText(chat_session_id)
        audio_analysis_results = await audio.mergeAndAnalyzeAudio(chat_session_id)
        video_analysis_results = await video.mergeAndAnalyzeVideo(chat_session_id)
        # todo Delete all the chatSessionMessages
        # TODO run the analysis inside the functions (video) and then compare the results and save it to the db
        pass

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        employee_id = self.scope['url_route']['kwargs']['employee_id']
        session = self.scope["session"]
        chat_session_id = session['session_id']
        name = uuid.uuid4()
        try:
            if text_data:
                message = json.loads(text_data)
                answer = await (chatbot.compute_answer(session, message['data'], employee_id))
                await chat.createChatSessionMessage(chat_session_id, message['data'], answer, None, None)
                await self.send(json.dumps({"answer_chatbot": answer, "question": message['data'], "type": 'text'}))
            if bytes_data:
                kind = filetype.guess(bytes_data)
                if kind.extension == 'wav':
                    audio_file = bytes_data
                    audio_path = audio.save_audio(chat_session_id, audio_file, name) #add path to return of save audio
                    text = audio.speech_to_text(chat_session_id, name)
                    answer = await chatbot.compute_answer(session, text, employee_id)
                    await chat.createChatSessionMessage(chat_session_id, text, answer, audio_path, None)
                    await self.send(json.dumps({"answer_chatbot": answer, "question": text, "type": 'media'}))
                elif kind.extension == 'mkv':
                    video_file = bytes_data
                    video_path = video.save_video(chat_session_id, video_file, name)
                    audio_path = audio.video_to_audio(chat_session_id, name)
                    text = audio.speech_to_text(chat_session_id, name)
                    answer = await chatbot.compute_answer(session, text, employee_id)
                    await chat.createChatSessionMessage(chat_session_id, text, answer, audio_path, video_path)
                    await self.send(json.dumps({"answer_chatbot": answer, "question": text, "type": 'media'}))
        except Exception as e:
            print(e)

