from rest_framework import serializers
from .models import Employer, Employee, StressRecord,  AppUsers,  Emotion
from dj_rest_auth.serializers import UserDetailsSerializer

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'surname', 'birthday', 'stressed', 'firstSession', 'company', 'user', 'coins']


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
        fields = ['id', 'topic_id', 'employee', 'answer']


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name', 'start_question']


class PrizeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name', 'description', 'rare', 'wheel']


class WheelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'company']


class AppUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUsers
        fields = ['id', 'email']


class ChatSessionMessageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['date', 'video_url', 'audio_url', 'text', 'chatbot_answer', 'date']


class EmotionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emotion
        fields = ['id', 'emotion_name', 'extended_name']

class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'employee', 'date', 'first_prevailing_emotion', 'second_prevailing_emotion', 'full_conversation_path', "full_video_path", "full_audio_path", 'analyzed', 'completed']








