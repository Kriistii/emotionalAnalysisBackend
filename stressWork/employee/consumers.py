from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
import uuid
from .services import chatbot, video, audio, text_service, chat
from .models import ChatSession, ChatSessionMessage, Employee, EmployeeTopic, Topic
import filetype

from semantic_text_similarity.models import WebBertSimilarity
web_model = WebBertSimilarity(device='cpu', batch_size=10)


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
        employee_id = self.scope['url_route']['kwargs']['employee_id']
        await chat.completeChat(chat_session_id, employee_id)
        # todo Delete all the chatSessionMessages
        # TODO run the analysis inside the functions (video) and then compare the results and save it to the db
        pass

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        employee_id = self.scope['url_route']['kwargs']['employee_id']
        session = self.scope["session"]
        chat_session_id = session['session_id']
        name = uuid.uuid4()
        text = None
        answer = None
        response = None
        video_path = None
        audio_path = None
        type = None
        try:
            if text_data:
                type = 'text'
                message = json.loads(text_data)
                text = message['data']
                answer = await (chatbot.compute_answer(session, text, employee_id))
                response = json.dumps({"answer_chatbot": answer, "question": text, "type": type})
            if bytes_data:
                kind = filetype.guess(bytes_data)
                if kind.extension == 'wav':
                    type = 'media'
                    audio_file = bytes_data
                    audio_path = audio.save_audio(chat_session_id, audio_file, name) #add path to return of save audio
                    text = audio.speech_to_text(chat_session_id, name)
                    answer = await chatbot.compute_answer(session, text, employee_id)
                    response = json.dumps({"answer_chatbot": answer, "question": text, "type": type})
                elif kind.extension == 'mkv':
                    type = 'media'
                    video_file = bytes_data
                    video_path = video.save_video(chat_session_id, video_file, name)
                    audio_path = audio.video_to_audio(chat_session_id, name)
                    text = audio.speech_to_text(chat_session_id, name)
                    answer = await chatbot.compute_answer(session, text, employee_id)
                    response = json.dumps({"answer_chatbot": answer, "question": text, "type": type})
            if session.get('topicAnswer', None):
                topic = session['topic']
                predict = web_model.predict([(topic['name'], text)])

                if predict <= 1:
                    answer = "Please answer to the question I made to you in a clear way."
                    response = json.dumps({"answer_chatbot": answer, "question": text, "type": type})
                else:
                    await chatbot.addNewEmployeeTopic(topic['id'], employee_id, text)
                    answer = await chatbot.compute_answer(session, text, employee_id)
                    response = json.dumps(
                        {"answer_chatbot": answer,
                         "question": text, "type": type})
                    del session['topicAnswer']
                    del session['topic']
            if session.get('topicQuestion', None):
                session['topicAnswer'] = True
                del session['topicQuestion']
            await chat.createChatSessionMessage(chat_session_id, text, answer, audio_path, video_path)
            await self.send(response)

        except Exception as e:
            print(e)

