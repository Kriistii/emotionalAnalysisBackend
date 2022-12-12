from asgiref.sync import sync_to_async
from ..models import Employee, ChatSession, ChatSessionMessage
from datetime import datetime


@sync_to_async
def createChatSession(session_id, employee_id):
    session = ChatSession(id=session_id, employee=Employee(pk=employee_id), date=datetime.now())
    session.save()


@sync_to_async
def createChatSessionMessage(session_id, text, answer, audio, video):
    message = ChatSessionMessage(session=ChatSession(pk=session_id), text=text,
                                 chatbot_answer=answer, date=datetime.now(), audio_url=audio,
                                 video_url=video)
    message.save()


@sync_to_async
def completeChat(session_id):

    chatSession = ChatSession.objects.get(pk=session_id)
    chatSession.completed = True
    chatSession.save()
