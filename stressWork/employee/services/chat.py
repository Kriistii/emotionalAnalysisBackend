from asgiref.sync import sync_to_async
from ..models import Employee, ChatSession, ChatSessionMessage
from ..serializers import *
from ..scheduler import *
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
def completeChat(session_id, employee_id):

    chatSession = ChatSession.objects.get(pk=session_id)
    chat_messages = ChatSessionMessage.objects.filter(session=chatSession)
    if len(chat_messages) == 0:
        chatSession.delete()
    else:
        employee = chatSession.employee
        #If first session after being stress-analyzed
        print(employee.firstSession)
        if employee.firstSession:
            scheduler.add_job(stressAnalysis, 'date', run_date=datetime.now() + timedelta(days=15),
                              name='stress_analysis', args=[employee_id], jobstore='default')
            employee.firstSession = False
            employee.save()

        chatSession.completed = True
        chatSession.save()
