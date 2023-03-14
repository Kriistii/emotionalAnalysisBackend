from asgiref.sync import sync_to_async
from ..models import Employee, Session, Request
from ..serializers import *
from ..scheduler import *
from datetime import datetime


def createSession(employee_id, request_id):
    session = Session(employee=Employee(pk=employee_id), request=Request(pk=request_id),
                      date=datetime.now())
    session.save()
    return session


@sync_to_async
def completeSession(session_id):
    session = Session.objects.get(pk=session_id)
    session.completed = True
    session.save()
