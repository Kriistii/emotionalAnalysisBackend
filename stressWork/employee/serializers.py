from rest_framework import serializers
from .models import Employee, StressRecord


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'surname', 'birthday']


class StressRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StressRecord
        fields = ['date', 'stressedUsers']
