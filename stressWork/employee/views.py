import django
from django.db.models import Max, Count
from rest_framework.status import HTTP_400_BAD_REQUEST

from .serializers import *
from .models import *
from .services import audio, video, session
import uuid
from datetime import datetime, timedelta
#from semantic_text_similarity.models import WebBertSimilarity

from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

#web_model = WebBertSimilarity(device='cpu', batch_size=10)
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from pandas import *

import json
import random


class EmployeeStatsAPIView(APIView):
    #   permission_classes = (IsAuthenticated,)
    def get(self, request):
        companyId = request.session['companyId']
        numEmployees = Employee.objects.filter(company=companyId).count()
        activeEmployees = Employee.objects.filter(id__in=Session.objects.values_list('employee_id', flat=True)).count()

        return Response({
            "numEmployees": numEmployees,
            "activeEmployees": activeEmployees
        })


class NewEmployee(APIView):
    def post(self, request):
        request.data['company'] = request.session['companyId']

        user = AppUsers.objects.create(email=request.data['email'], password=request.data['password'], is_active=True,
                                       is_staff=False,
                                       is_superuser=False)
        request.data['user'] = user.id
        request.data['step'] = 0

        serializer = EmployeeStepSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(request.data['password'])
            user.save()
            serializer.save()

            return Response(status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegistrationForm(APIView):
    def post(self, request):
        employee = get_object_or_404(Employee, id=request.data['employee'])
        employeeData = request.data['data']
        employeeData['step'] = 1
        serializer = EmployeeGeneralSerializer(employee,data=employeeData)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetStep(APIView):
    def post(self, request):
        employee = get_object_or_404(Employee, id=request['employee_id'])
        serializer = EmployeeStepSerializer(employee)

        return Response(serializer.data)

class NewRequest(APIView):
    def post(self, request):
        textField = request.data['text']
        employer = request.data['employer_id']

        Request.objects.create(text=textField, created_by=employer['id'], created_at=datetime.now())

        return Response('Ok')


class StressStats(APIView):
    def get(self, request):
        stats = Employee.objects.annotate(sessions=Count('session__id'))
        print(stats)

        return Response(stats)


class StressStatsTimespan(APIView):
    def get(self, request, timespan):

        today = datetime.today()

        if timespan == "week":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=7)

            stats = Session.objects.filter(date__gte=week_start, date__lt=week_end)
        elif timespan == "month":
            stats = Session.objects.filter(date__month=today.month, date__year=today.year)
        elif timespan == "year":
            stats = Session.objects.filter(date__year=today.year)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        stats = stats.order_by('date')

        serializer = SessionSerializer(stats, many=True)

        return Response(serializer.data)


class GetInteractionSummary(APIView):
    def get(self, request):
        company_id = request.session['companyId']

        # query = "SELECT id, name, surname, is_stressed, max(date) FROM employees natural join chatsession WHERE company = %s GROUP BY id, name, surname, is_stressed"

        result = Session.objects\
                .filter(employee__company=company_id)\
                .values('employee__id', 'employee__name', 'employee__surname', 'employee__stressed')\
                .annotate(lastDate=Max('date'), sessions=Count('id'))\
                .order_by('employee__name', 'employee__surname')

        return Response(result)

class GetUserInteractions(APIView):
    def get(self, request, employee_id):
        # query = "SELECT id, date, first_prevailing_emotion FROM chatsession WHERE employee=%d ORDER BY date DESC"

        result = Session.objects.filter(employee=employee_id, analyzed=True).order_by("-date")
        serializer = SessionSerializer(result, many=True).data

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
        request_id = request.data.get('request_id', None)
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
            return Response("Success")
        return response

class CompleteNewRequest(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        employee_id = request.data.get('employee_id', None)
        notCompletedRequests = Request.objects.exclude(id__in=
                               Session.objects.filter(employee_id=employee_id).values_list('request_id', flat=True))
        if(notCompletedRequests.count() == 0):
            return Response(400)
        max = notCompletedRequests.count() - 1
        min = 0
        n = random.randint(min, max)
        serializer = RequestOnlyTextSerializer(notCompletedRequests[n])
        print(serializer.data)
        return Response(serializer.data)
class GetQuestionnaireRequest(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        employee_id = request.data.get('employee_id', None)

        notCompletedRequest = Request.objects.exclude(id__in=
                               Questionnaire.objects.filter(employee_id=employee_id).values_list('request_id',
                            flat=True)).filter(id__in=Session.objects.filter(employee_id=employee_id).values_list('request_id',
                            flat=True)).first()
        print(notCompletedRequest)
        serializer = RequestOnlyTextSerializer(notCompletedRequest)
        print(serializer.data)
        return Response(serializer.data)

class FillInQuestionnaire(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        print(request.data)

        employee_id = request.data.get('employee_id', None)
        request_id = request.data.get('request_id', None)
        happiness = request.data.get('happiness', None)
        sadness = request.data.get('sadness', None)
        anger = request.data.get('anger', None)
        fear = request.data.get('fear', None)
        surprise = request.data.get('surprise', None)
        emotion_ids = [1, 2, 3, 4, 5]
        emotion_score = [anger, fear, happiness, sadness, surprise]
        for key, value in enumerate(emotion_ids):
            questionnaire = Questionnaire(employee=Employee(pk=employee_id), request=Request(pk=request_id),
                              emotion=Emotion(pk=value), score=emotion_score[key])
            questionnaire.save()

        return Response('Ok')

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
    def get(self, request, employee_id):
        chats = SessionMiniSerializer(get_list_or_404(Session.objects.filter(employee=get_object_or_404(Employee, pk=employee_id), analyzed=True).order_by("-date")), many=True).data
        return Response({"chats": chats})

class RetrieveChatLogsEmployee(APIView):

    def post(self, request):
        session_id = request.data.get('chat_id', None)
        if session_id is not None:
            session_logs = SessionSerializerWithRequest(get_object_or_404(Session, pk=session_id)).data
            return Response({"logs": session_logs})


class InteractionDetailsAPIView(APIView):
    def get(self, request, session_id):
        session = get_object_or_404(Session, id=session_id)
        results = SessionResults.objects.filter(session_id=session_id)
        results = ResultsSerializerWithSession(results, many=True)
        results = results.data[:]
        response = {}
        for r in results:
            if(r['text'] == True):
                response['text_results'] = r
            if(r['audio'] == True):
                response['audio_results'] = r
            if(r['video'] == True):
                response['video_results'] = r
        csv_results = None
        serializer = SessionSerializer(session).data
        if(serializer['first_prevailing_emotion']):
            firstEmotion = get_object_or_404(Emotion, id=serializer['first_prevailing_emotion'])
            serializer['first_prevailing_emotion'] = EmotionsSerializer(firstEmotion).data['extended_name']
        if(serializer['second_prevailing_emotion']):
            secondEmotion = get_object_or_404(Emotion, id=serializer['second_prevailing_emotion'])
            serializer['second_prevailing_emotion'] = EmotionsSerializer(secondEmotion).data['extended_name']
        if(serializer['full_video_path']):
            serializer['hasGraph'] = True
            data = read_csv("tmp/{}/video_analysis.csv".format(session_id))

            hp = data['hp']
            fr = data['fr']
            an = data['an']
            sd = data['sd']
            sr = data['sr']

            maximum_score = max(hp.max(), fr.max(),an.max(), sd.max(), sr.max())

            csv_results = {'Happiness': hp.tolist(), 'Fear': fr.tolist(), 'Anger': an.tolist(), 'Sadness': sd.tolist(),
                           'Surprise': sr.tolist(),'length_conversation': len(data.index),
                           'maximum_emotion_score': maximum_score}
        else:
            serializer['hasGraph'] = False

        employee = get_object_or_404(Employee, id=serializer['employee'])
        serializerEmployee = EmployeeSerializer(employee).data


        return Response(data={"analysis": serializer, "empl_info": serializerEmployee, "csv_results" : csv_results,
                              'text' : response['text_results'], 'audio' : response['audio_results'],
                              'video' : response['video_results']}, status=status.HTTP_200_OK)


