import django
from django.db.models import Max

from .serializers import *
from .models import *
from .services import audio, video, session
import uuid
from datetime import datetime, timedelta
from semantic_text_similarity.models import WebBertSimilarity

from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

web_model = WebBertSimilarity(device='cpu', batch_size=10)
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from pandas import *

import json


class EmployeeStatsAPIView(APIView):
    #   permission_classes = (IsAuthenticated,)
    def get(self, request):
        companyId = request.session['companyId']

        numEmployees = Employee.objects.filter(company=companyId).count()
        stressedEmployees = Employee.objects.filter(stressed=True, company=companyId).count()

        return Response({
            "numEmployees": numEmployees,
            "stressedEmployees": stressedEmployees
        })


class NewEmployee(APIView):
    def post(self, request):
        request.data['company'] = request.session['companyId']

        user = AppUsers.objects.create(email=request.data['email'], password=request.data['password'], is_active=True,
                                       is_staff=False,
                                       is_superuser=False)
        request.data['user'] = user.id

        serializer = EmployeeSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(request.data['password'])
            user.save()
            serializer.save()

            return Response(status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StressStats(APIView):
    def get(self, request):
        stats = StressRecord.objects.all()
        serializer = StressRecordSerializer(stats, many=True)

        return Response(serializer.data)


class StressStatsTimespan(APIView):
    def get(self, request, timespan):
        companyId = request.session['companyId']

        today = datetime.today()
        serializer = StressRecordSerializer(data=request.data)

        if timespan == "week":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=7)

            stats = StressRecord.objects.filter(date__gte=week_start, date__lt=week_end, company=companyId)
        elif timespan == "month":
            stats = StressRecord.objects.filter(date__month=today.month, date__year=today.year, company=companyId)
        elif timespan == "year":
            stats = StressRecord.objects.filter(date__year=today.year, company=companyId)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        stats = stats.order_by('date')

        serializer = StressRecordSerializer(stats, many=True)

        return Response(serializer.data)


class GetInteractionSummary(APIView):
    def get(self, request):
        company_id = request.session['companyId']

        # query = "SELECT id, name, surname, is_stressed, max(date) FROM employees natural join chatsession WHERE company = %s GROUP BY id, name, surname, is_stressed"

        result = ChatSession.objects\
                .filter(employee__company=company_id)\
                .values('employee__id', 'employee__name', 'employee__surname', 'employee__stressed')\
                .annotate(lastDate=Max('date'))\
                .order_by('employee__name', 'employee__surname')

        return Response(result)

class GetUserInteractions(APIView):
    def get(self, request, employee_id):
        # query = "SELECT id, date, first_prevailing_emotion FROM chatsession WHERE employee=%d ORDER BY date DESC"

        result = ChatSession.objects.filter(employee=employee_id, analyzed=True).order_by("-date")
        serializer = ChatSessionSerializer(result, many=True).data

        for s in serializer:
            firstEmotion = get_object_or_404(Emotion, id=s['first_prevailing_emotion'])
            s['first_prevailing_emotion'] = EmotionsSerializer(firstEmotion).data['extended_name']

        return Response(serializer)

class EmployeeAPIView(APIView):

    def get(self, request):
        employee = Employee.objects.all()
        item = self.request.query_params.get("item", "")

        if item != "":
            employee = employee.filter(name=item)

        serializer = EmployeeSerializer(employee, many=True)

        return Response(serializer.data)

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeDetailAPIView(APIView):

    def get(self, request, employee_id):
        employee = get_object_or_404(Employee, id=employee_id)
        serializer = EmployeeSerializer(employee)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class NewSession(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        name = uuid.uuid4()
        request_id = 1
        employee_id = request.data.get('employee_id', None)
        response = Response("Error")
        if request.FILES.get('video-blob', None):
            newSession = session.createSession(employee_id, request_id)
            session_id = newSession.id
            video_file = request.FILES['video-blob']
            video_path = video.save_video(session_id, video_file, name)
            audio_path = audio.video_to_audio(session_id, name)
            text = audio.speech_to_text(session_id, name)
            newSession.full_video_path = video_path
            newSession.full_audio_path = audio_path,
            newSession.text = text
            newSession.save()
            #kot fare
            return Response("Success")
        return response

class CreateEmployeeAPIView(APIView):
    # TODO request filter
    def post(self, request):
        if request.POST.get('email', None):
            emailField = request.POST['email']
        if request.POST.get('name', None):
            nameField = request.POST['name']
        if request.POST.get('surname', None):
            surnameField = request.POST['surname']
        if request.POST.get('birthday', None):
            birthdayField = request.POST['birthday']
        if request.POST.get('company', None):
            companyField = Company.objects.get(id=request.POST['company'])
        if request.POST.get('password', None):
            passwordField = make_password(request.POST['password'])
        stressedField = 0

        user = AppUsers.objects.create(email=emailField, password=passwordField, is_active=True, is_staff=False,
                                       is_superuser=False)
        user.save()
        employee = Employee.objects.create(birthday=birthdayField,
                                           name=nameField, surname=surnameField, company=companyField,
                                           stressed=stressedField, user=user)

        employee.save()
        return Response("Ok")
class CreateRequestAPIView(APIView):
    # TODO request filter
    def post(self, request):
        if request.POST.get('text', None):
            textField = request.POST['text']
            request = Request.objects.create(text=textField, created_at=datetime.now(), created_by=request.user.id)
            request.save()
            return Response("Ok")

        return Response("Error")


class CreateEmployerAPIView(APIView):
    def post(self, request):
        if request.POST.get('email', None):
            emailField = request.POST['email']
        if request.POST.get('name', None):
            nameField = request.POST['name']
        if request.POST.get('surname', None):
            surnameField = request.POST['surname']
        if request.POST.get('birthday', None):
            birthdayField = request.POST['birthday']
        if request.POST.get('company', None):
            companyField = Company.objects.get(id=request.POST['company'])
        if request.POST.get('password', None):
            passwordField = make_password(request.POST['password'])

        user = AppUsers.objects.create(email=emailField, password=passwordField, is_active=True, is_staff=True,
                                       is_superuser=False)
        user.save()
        employer = Employer.objects.create(birthday=birthdayField,
                                           name=nameField, surname=surnameField, company=companyField, user=user)

        employer.save()
        return Response("Ok")


class TestVideoAnalysisAPIView(APIView):
    # todo request filter
    def get(self, request):
        name = 1
        video.analyze_video(name)
        return Response("Ok")


class RetrieveEmployeeInformation(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_id = request.data.get('user_id', None)
        if user_id is not None:
            emp = EmployeeSerializer(get_object_or_404(Employee, user=get_object_or_404(AppUsers, pk=user_id))).data
            return Response({"employee": emp})
        else:
            return Response("User id not found")

class RetrieveEmployerInformation(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_id = request.data.get('user_id', None)
        if user_id is not None:
            emp = EmployerSerializer(get_object_or_404(Employer, user=get_object_or_404(AppUsers, pk=user_id))).data
            request.session['companyId'] = emp['company']

            return Response({"employer": emp})
        else:
            return Response("User id not found")

class TimeChatOverEmployee(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_id = request.data.get('user_id', None)
        if user_id is not None:
            today = datetime.today()

            year = today.year
            month = today.month
            day = today.day
            number_chats = ChatSessionSerializer(ChatSession.objects.filter(employee=get_object_or_404(Employee, pk=user_id), date__year=year,
                                date__month=month, date__day=day, completed=True), many=True).data
            print(len(number_chats))
            if len(number_chats) >= 2:
                return Response({"text1": "Congratulations, we just talked for 3 minutes! Unfortunately you already "
                                          "got 2 coins today, so I can't give you another one. But I am really happy "
                                          "that we talked again.", "text2": "You can now stop the chat or continue "
                                                                            "talking with me!", "coin": False})
            else:
                employee = Employee.objects.get(pk=user_id)
                employee.coins = employee.coins + 1
                employee.save()
                return Response({"text1": "Congratulations, we just talked for 3 minutes! I just added one coin "
                                          "to your balance to thank you for the time you spent talking with me. You will be able to "
                                          "see it when you close the chat using the X on the top right! "
                                    , "text2": "You can now stop the chat or continue "
                                               "talking with me!", "coin": True})
        else:
            return Response("User id not found", status=404)

class RetrieveSessionsEmployee(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_id = request.data.get('user_id', None)
        if user_id is not None:
            chats = SessionSerializer(get_list_or_404(Session.objects.filter(employee=get_object_or_404(Employee, pk=user_id), analyzed=True).order_by("-date")), many=True).data
            return Response({"chats": chats})

class RetrieveChatLogsEmployee(APIView):

    def post(self, request):
        chat_id = request.data.get('chat_id', None)
        if chat_id is not None:
            chat_logs = ChatSessionSerializer(get_object_or_404(ChatSession, pk=chat_id)).data
            conversation_path = default_storage.path(chat_logs['full_conversation_path'])
            f = open(conversation_path)
            logs = json.load(f)
            return Response({"chat": logs, "date": chat_logs['date']})


class InteractionDetailsAPIView(APIView):
    def get(self, request, chat_id):
        chat_session = get_object_or_404(ChatSession, id=chat_id)
        csv_results = None;
        serializerChat = ChatSessionSerializer(chat_session).data
        if(serializerChat['first_prevailing_emotion']):
            firstEmotion = get_object_or_404(Emotion, id=serializerChat['first_prevailing_emotion'])
            serializerChat['first_prevailing_emotion'] = EmotionsSerializer(firstEmotion).data['extended_name']
        if(serializerChat['second_prevailing_emotion']):
            secondEmotion = get_object_or_404(Emotion, id=serializerChat['second_prevailing_emotion'])
            serializerChat['second_prevailing_emotion'] = EmotionsSerializer(secondEmotion).data['extended_name']
        if(serializerChat['full_video_path']):
            serializerChat['hasGraph'] = True
            data = read_csv("tmp/{}/video_analysis.csv".format(chat_id))

            hp = data['hp']
            fr = data['fr']
            an = data['an']
            sd = data['sd']
            sr = data['sr']

            maximum_score = max(hp.max(), fr.max(),an.max(), sd.max(), sr.max())

            csv_results = {'Happiness': hp.tolist(), 'Fear': fr.tolist(), 'Anger': an.tolist(), 'Sadness': sd.tolist(), 'Surprise': sr.tolist(),
                           'length_conversation': len(data.index), 'maximum_emotion_score': maximum_score}
        else:
            serializerChat['hasGraph'] = False

        employee = get_object_or_404(Employee, id=serializerChat['employee'])
        serializerEmployee = EmployeeSerializer(employee).data


        return Response(data={"analysis": serializerChat, "empl_info": serializerEmployee, "csv_results" : csv_results}, status=status.HTTP_200_OK)


