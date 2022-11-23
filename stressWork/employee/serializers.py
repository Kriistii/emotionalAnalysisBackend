from rest_framework import serializers
from .models import Employee, StressRecord, EmployeeTopic, Topic


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'surname', 'birthday']


class StressRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StressRecord
        fields = ['date', 'stressedUsers']

class EmployeeTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeTopic
        fields = ['id', 'topic_id', 'employee_id', 'answer']

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name', 'start_question']

