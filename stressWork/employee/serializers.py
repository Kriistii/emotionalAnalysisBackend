from rest_framework import serializers
from .models import Employer, Employee, StressRecord, EmployeeTopic, Topic, Prize, Wheel, AppUsers, ChatSessionMessage, ChatSession
from dj_rest_auth.serializers import UserDetailsSerializer

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'surname', 'birthday', 'company',  'coins']


class EmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = ['id', 'name', 'surname', 'birthday', 'company', 'user']  # TODO: manage null errors


class StressRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StressRecord
        fields = ['date', 'stressedUsers']


class EmployeeTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeTopic
        fields = ['id', 'topic_id', 'employee', 'answer']


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name', 'start_question']


class PrizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prize
        fields = ['id', 'name', 'description', 'rare', 'wheel']


class WheelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wheel
        fields = ['id', 'company_id']


class AppUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUsers
        fields = ['id', 'email']


class ChatSessionMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSessionMessage
        fields = ['date', 'video_url', 'audio_url', 'text', 'chatbot_answer', 'date']

class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['id', 'date', 'first_prevailing_emotion', 'second_prevailing_emotion', 'analyzed', 'full_conversation_path']








