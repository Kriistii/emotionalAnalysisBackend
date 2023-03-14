from rest_framework import serializers
from .models import Employer, Employee, StressRecord,  AppUsers,  Emotion
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
        fields = ['id', 'employee', 'date', 'request', 'analyzed']








