from asgiref.sync import sync_to_async
from ..models import Employee, Session, Request
from ..serializers import *
from ..scheduler import *
from datetime import datetime


@sync_to_async
def createSession(session_id, employee_id, request_id, video_path, audio_path, text_path):
    session = Session(id=session_id, employee=Employee(pk=employee_id), request=Request(pk=request_id),
                      date=datetime.now(), full_video_path=video_path, full_audio_path=audio_path,
                      text=text_path)
    session.save()


@sync_to_async
def completeSession(session_id):
    session = Session.objects.get(pk=session_id)
    session.completed = True
    session.save()
