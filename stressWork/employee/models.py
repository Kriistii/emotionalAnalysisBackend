from django.db import models
from django import db
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from .managers import CustomUserManager

class Company(models.Model):
    class Meta:
        db_table = 'companies'
    company_name = models.CharField(max_length=50)
    active_users_number = models.IntegerField()
    country = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.company_name}"

class Employer(models.Model):
    class Meta:
        db_table = 'employers'
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    birthday = models.DateField()
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    user = models.ForeignKey("AppUsers", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.name + self.surname}"


class Employee(models.Model):
    class Meta:
        db_table = 'employees'
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    birthday = models.DateField()
    stressed = models.BooleanField(default=False)
    firstSession = models.BooleanField(default=True)
    company = models.ForeignKey("Company", on_delete=models.CASCADE)  
    user = models.ForeignKey("AppUsers", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.name + ' ' + self.surname}"

class AppUsers(AbstractBaseUser, PermissionsMixin):
    class Meta:
        db_table = 'app_users'
    REQUIRED_FIELDS = ['password']
    USERNAME_FIELD = ('email')
    password = models.CharField(max_length=200)
    email = models.EmailField(max_length=20, unique=True)
    is_staff = models.BooleanField(null=True)
    is_superuser = models.BooleanField(null=True)
    is_active = models.BooleanField(null=True)

    objects = CustomUserManager()

    def __str__(self) -> str:
        return f"{self.email, self.is_staff}"

class Emotion(models.Model):
    class Meta:
        db_table = 'emotion'
    emotion_name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.emotion_name}"

class ChatSession(models.Model):
    class Meta:
        db_table = 'chat_session'

    employee = models.ForeignKey("Employee", on_delete=models.CASCADE)
    date = models.DateTimeField()
    first_prevailing_emotion = models.ForeignKey("Emotion", related_name="first_prevailing_emotion",                                       on_delete=models.DO_NOTHING)
    second_prevailing_emotion = models.ForeignKey("Emotion", related_name="second_prevailing_emotion",                                            on_delete=models.DO_NOTHING)
    full_video_path = models.CharField(max_length=50)
    full_audio_path = models.CharField(max_length=50)
    full_conversation_path = models.TextField()

    def __str__(self) -> str:
        return f"{self.employee + ' date:' + self.date}"


class ChatSessionMessage(models.Model):
    class Meta:
        db_table = 'chat_session_message'
    session = models.ForeignKey("ChatSession", on_delete=models.CASCADE)
    date = models.DateTimeField()
    video_url = models.CharField(max_length=50)
    audio_url = models.CharField(max_length=50)
    text = models.TextField()
    chatbot_answer = models.TextField()

    def __str__(self) -> str:
        return f"{self.session_id + ' date:' + self.date}"

class StressRecord(models.Model):
    class Meta:
        db_table = 'stress_record'
    date = models.DateField(auto_now=True)
    stressedUsers = models.IntegerField()
    #prova

    def __str__(self):
        return f"{self.date + ' stressed:' + self.stressedUsers}"


class Wheel(models.Model):
    class Meta:
        db_table = 'wheel'
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    def __str__(self) -> str:
        return f"{self.company + ' date:' + self.date}"


class Prize(models.Model):
    class Meta:
        db_table = 'prize'
    name = models.CharField(max_length=30)
    description = models.TextField(max_length=100)
    rare = models.BooleanField(default=False)
    wheel = models.ForeignKey("Wheel", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{'name' + str(self.name) + ' description:' + str(self.description)}"


class EmployeePrize(models.Model):
    class Meta:
        db_table = 'employee_prize'
    date = models.DateTimeField()
    prize = models.ForeignKey("Prize", on_delete=models.CASCADE)
    employee = models.ForeignKey("Employee", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{'employee' + self.employee_id + ' prize:' + self.prize_id + ' date:' + self.date}"

class Topic(models.Model):
    class Meta:
        db_table = 'topic'
    name = models.CharField(max_length=30)
    start_question = models.TextField(max_length=50)

    def __str__(self) -> str:
        return f"{'id:' + str(self.pk) + ' name:' + str(self.name) + ' start_question: ' + str(self.start_question)}"


class EmployeeTopic(models.Model):
    class Meta:
        db_table = 'employee_topic'
    answer = models.TextField(max_length=100)
    topic = models.ForeignKey("Topic", on_delete=models.CASCADE)
    employee = models.ForeignKey("Employee", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"employe: {self.employee} topic: {self.topic} answer: {self.answer}"
