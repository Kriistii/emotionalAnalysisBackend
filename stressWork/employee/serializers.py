from rest_framework import serializers
from .models import Employee, Record

class EmployeeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Employee
        fields = ['id', 'name', 'surname', 'birthday']

class RecordSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Record
        fields = ['id', 'datetime', 'score', 'employee']