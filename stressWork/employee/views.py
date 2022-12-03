from .serializers import EmployeeSerializer, StressRecordSerializer
from .models import Employee, StressRecord
from .services import audio, chatbot, video
import uuid
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth.hashers import make_password

class EmployeeStatsAPIView(APIView):
    def get(self, request):
        numEmployees = Employee.objects.count()
        stressedEmployees = Employee.objects.filter(stressed=True).count()

        return Response({
            "numEmployees": numEmployees,
            "stressedEmployees": stressedEmployees
        })


class NewEmployer(APIView):
    def post(self, request):
        request.data['company_id'] = request.session.get("companyId")  # TODO: add companyId to session on employer login

        serializer = EmployerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewWheel(APIView):
    def post(self, request):
        request.data['company_id'] = request.session.get("companyId")  # TODO: add companyId to session on employer login

        serializer = WheelSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetWheels(APIView):
    def get(self, request):
        wheels = Wheel.objects.filter(
            company_id=request.session.get("companyId"))  # TODO: add companyId to session on employer login
        serializer = WheelSerializer(wheels, many=True)

        return Response(serializer.data)


class NewPrize(APIView):
    def post(self, request, wheel_id):
        request.data['wheel_id'] = wheel_id

        serializer = PrizeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditPrize(APIView):
    def post(self, request, prize_id):
        prize = Prize.objects.get(id=prize_id)
        prize.name = request.data['name']
        prize.description = request.data['description']
        prize.rare = request.data['rare']

        prize.save()

        return Response(status=status.HTTP_200_OK)


class DelPrize(APIView):
    def post(self, request, prize_id):
        Prize.objects.filter(id=prize_id).delete()  # TODO: add checks?

        return Response(status=status.HTTP_200_OK)


class GetPrizes(APIView):
    def get(self, request, wheel_id):
        prizes = Prize.objects.filter(wheel_id=wheel_id)
        serializer = PrizeSerializer(prizes, many=True)

        return Response(serializer.data)


class StressStats(APIView):
    def get(self, request):
        stats = StressRecord.objects.all()
        serializer = StressRecordSerializer(stats, many=True)

        return Response(serializer.data)

class StressStatsTimespan(APIView):
    def get(self, request, timespan):
        today = datetime.today()
        serializer = StressRecordSerializer(data=request.data)

        if timespan == "week":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=7)

            stats = StressRecord.objects.filter(date__gte=week_start, date__lt=week_end)
        elif timespan == "month":
            stats = StressRecord.objects.filter(date__month=today.month)
        elif timespan == "year":
            stats = StressRecord.objects.filter(date__year=today.year)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        stats = stats.order_by('date')

        serializer = StressRecordSerializer(stats, many=True)

        return Response(serializer.data)


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


class NewRecordAPIView(APIView):
    def post(self, request, employee_id):
        name = uuid.uuid4()
        text = ''
        response = Response("Error")
        if request.FILES.get('video-blob', None):
            video_file = request.FILES['video-blob']
            video.save_video(video_file, name)
            video.analyze_video(name)
            audio.video_to_audio(name)
            text = audio.speech_to_text(name)
            answer = chatbot.compute_answer(request, text, employee_id)
            response = Response({"answer_chatbot": answer, "question": text})

        if request.FILES.get('audio-blob', None):
            audio_file = request.FILES['audio-blob']
            audio.save_audio(audio_file, name)
            # audio.analyze_audio(name)
            text = audio.speech_to_text(name)
            answer = chatbot.compute_answer(request, text, employee_id)
            response = Response({"answer_chatbot": answer, "question": text})

        if request.POST.get('text', None):
            text = request.POST['text']
            # analyzeText(text)
            answer = chatbot.compute_answer(request, text, employee_id)
            response = Response({"answer_chatbot": answer, "question": text})

        print(request.session.get('topicAnswer', None))
        if request.session.get('topicAnswer', None):
            topic = request.session['topic']
            # TODO Analyz the answer wrt of the topic and save the answer in the database
            predict = web_model.predict([(topic['name'], text)])
            if predict <= 1:
                response = Response(
                    {"answer_chatbot": "Please answer to the question I made to you in a clear way.", "question": text})
            else:
                EmployeeTopic.objects.create(topic=Topic(pk=topic['id']), employee=Employee(pk=employee_id),
                                             answer=text)
                answer = chatbot.compute_answer(request, text, employee_id)
                response = Response({"answer_chatbot": answer, "question": text})
                del request.session['topicAnswer']
                del request.session['topic']

        if request.session.get('topicQuestion', None):
            request.session['topicAnswer'] = True
            del request.session['topicQuestion']
        print(request.session.get('topicAnswer', None))

        return response

class StartChatAPIView(APIView):
    def get(self, request, employee_id):
        e = Employee.objects.get(id=employee_id)
        employee = EmployeeSerializer(Employee.objects.get(id=employee_id))
        if employee['firstSession']:
            return chatbot.start_fsession_message
        else:
            e.firstSession = False
            e.save()
            return chatbot.start_message


class CreateEmployeeAPIView(APIView):
    #todo request filter
    def post(self, request):
        if request.POST.get('email', None):
            emailField = request.POST['email']
        if request.POST.get('name', None):
            nameField = request.POST['name']
        if request.POST.get('surname', None):
            surnameField = request.POST['surname']
        if request.POST.get('birthday', None):
            birthdayField = request.POST['birthday']
        if request.POST.get('company_id', None):
            companyField = Company.objects.get(id = request.POST['company_id'])
        if request.POST.get('password', None):
            passwordField = make_password(request.POST['password'])
        stressedField = 0

        employee = Employee.objects.create(email = emailField, password = passwordField, birthday = birthdayField,
                                            name = nameField, surname = surnameField, company_id = companyField,
                                            stressed = stressedField)
        employee.save()
        return Response("Ok")

class CloseChatAPIView(APIView):

    def get(self, request):
        chat_log = request.session.get('chat_log', None)
        topicAnswer = request.session.get('topicAnswer', None)
        topicQuestion = request.session.get('topicQuestion', None)
        topic = request.session.get('topic', None)
        if chat_log is not None:
            del request.session['chat_log']
        if topicAnswer is not None:
            del request.session['topicAnswer']
        if topicQuestion is not None:
            del request.session['topicQuestion']
        if topic is not None:
            del request.session['topic']
        # TODO Implement logic to start a cron for analyzing the data
        return Response("Chat closed")
