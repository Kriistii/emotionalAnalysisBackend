from rest_framework import serializers
from .models import Employer, Employee, StressRecord,  AppUsers,  Emotion, Session, Request, SessionResults, Questionnaire
from dj_rest_auth.serializers import UserDetailsSerializer

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'surname', 'age', 'stressed', 'company', 'user', 'step', 'session_no', 'username']

class EmployeeDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'surname', 'age', 'stressed', 'company', 'user', 'step', 'session_no', 'username']


class EmployeeGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['age', 'faculty', 'education', 'gender', 'step', 'session_no', 'username']


class EmployeeCodeSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ['name', 'surname', 'age', 'code']

    def get_code(self, obj):
        name = obj.name[:2].upper()
        surname = obj.surname[:2].upper()
        age = str(obj.age)
        return f"{name}{surname}{age}"


class EmployeeStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['step']
class EmployeeUserStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['name', 'surname','step', 'user', 'company', 'session_no']


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
        fields = ['text', 'audio', 'video', 'happiness', 'sadness', 'anger', 'fear', 'surprise', 'neutrality']

class QuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = ('happiness', 'sadness', 'anger', 'fear', 'surprise', 'neutrality', 'new_emotion', 'new_emotion_score')






