from rest_framework import serializers
from .models import Employer, Employee, StressRecord,  AppUsers,  Emotion, Session, Request, SessionResults
from dj_rest_auth.serializers import UserDetailsSerializer

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'surname', 'birthday', 'stressed', 'company', 'user', 'step']


class EmployeeStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['step']


class EmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = ['id', 'name', 'surname', 'birthday', 'company', 'user']  # TODO: manage null errors


class StressRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StressRecord
        fields = ['date', 'stressedUsers']

class AppUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUsers
        fields = ['id', 'email']


class EmotionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emotion
        fields = ['id', 'emotion_name', 'extended_name']

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'employee', 'date', 'request', 'analyzed', 'text', 'full_audio_path', 'full_video_path',
                  'first_prevailing_emotion', 'second_prevailing_emotion']


class SessionMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'employee', 'date']
class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ['id', 'text', 'created_at', 'created_by']
class RequestOnlyTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ['id', 'text']

class SessionSerializerWithRequest(serializers.ModelSerializer):
    request = RequestOnlyTextSerializer()
    class Meta:
        model = Session
        fields = ['id', 'employee', 'date', 'request', 'analyzed', 'text']
class ResultsSerializerWithSession(serializers.ModelSerializer):
    class Meta:
        model = SessionResults
        fields = ['text', 'audio', 'video', 'happiness', 'sadness', 'anger', 'fear', 'surprise']






