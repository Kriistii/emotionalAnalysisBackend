from .serializers import EmployeeSerializer, StressRecordSerializer
from .models import Employee, StressRecord
from .services import audio, chatbot, video
import uuid
from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

class EmployeeStatsAPIView(APIView):
    def get(self, request):
        numEmployees = Employee.objects.count()
        stressedEmployees = Employee.objects.filter(stressed=True).count()

        return Response({
            "numEmployees": numEmployees,
            "stressedEmployees": stressedEmployees
        })

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
    def post(self, request):
        name = uuid.uuid4()

        if request.FILES.get('video-blob', None):
            video_file = request.FILES['video-blob']
            video.save_video(video_file, name)
            audio.video_to_audio(name)
            text = audio.speech_to_text(name)
            answer = chatbot.compute_answer(request, text)
            return Response({"answer_chatbot": answer, "question": text})

        if request.FILES.get('audio-blob', None):
            # TODO implement logic for audio-blob only
            audio_file = request.FILES['audio-blob']
            audio.save_audio(audio_file, name)
            text = audio.speech_to_text(name)
            answer = chatbot.compute_answer(request, text)
            return Response({"answer_chatbot": answer, "question": text})

        if request.POST.get('text', None):
            text = request.POST['text']
            # analyzeText(text)
            answer = chatbot.compute_answer(request, text)
            return Response({"answer_chatbot": answer, "question": text})

        return Response("Error")

class CloseChatAPIView(APIView):

    def get(self, request):
        chat_log = request.session.get('chat_log', None)
        if chat_log is not None:
            del request.session['chat_log']
        #TODO Implement logic to start a cron for analyzing the data
        return Response("Chat closed")
            

