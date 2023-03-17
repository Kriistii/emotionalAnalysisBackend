from rest_framework import serializers
from .models import Employer, Employee, StressRecord,  AppUsers,  Emotion, Session, Request
from dj_rest_auth.serializers import UserDetailsSerializer

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'surname', 'birthday', 'stressed', 'company', 'user']


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
        fields = ['id', 'employee', 'date', 'request', 'analyzed', 'text', 'full_audio_path', 'full_video_path']
class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ['id', 'text', 'created_at', 'created_by']
class RequestOnlyTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = [ 'id','text']








