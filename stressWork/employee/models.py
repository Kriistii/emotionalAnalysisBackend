import uuid

from django.db import models
from django import db
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from .managers import CustomUserManager
import uuid


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
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    user = models.ForeignKey("AppUsers", on_delete=models.CASCADE)

    objects = models.Manager()

    def __str__(self) -> str:
        return f"{self.name + ' ' + self.surname}"


class AppUsers(AbstractBaseUser, PermissionsMixin):
    class Meta:
        db_table = 'app_users'

    REQUIRED_FIELDS = ['password']
    USERNAME_FIELD = ('email')
    password = models.CharField(max_length=200)
    email = models.EmailField(max_length=50, unique=True)
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
    extended_name = models.CharField(max_length=100)
    objects = models.Manager()

    def __str__(self) -> str:
        return f"{'emotion_name:' +  str(self.emotion_name) + 'extended_name:' + str(self.extended_name)}"

class Request(models.Model):
    class Meta:
        db_table = 'request'

    text = models.TextField(max_length=400)
    created_at = models.DateTimeField(null=True)
    created_by = models.IntegerField(null=True)
    objects = models.Manager()

    def __str__(self) -> str:
        return f"{'text:' +  str(self.text) + 'created_at:' + str(self.created_at)+ 'created_by:' + str(self.created_by)}"


class Session(models.Model):
    class Meta:
        db_table = 'chat_session'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)
    employee = models.ForeignKey("Employee", on_delete=models.CASCADE)
    request = models.ForeignKey("Request", on_delete=models.CASCADE)
    date = models.DateTimeField()
    first_prevailing_emotion = models.ForeignKey("Emotion", related_name="first_prevailing_emotion", null=True,
                                                 on_delete=models.DO_NOTHING)
    second_prevailing_emotion = models.ForeignKey("Emotion", related_name="second_prevailing_emotion", null=True,
                                                  on_delete=models.DO_NOTHING)
    full_video_path = models.CharField(max_length=200, null=True)
    full_audio_path = models.CharField(max_length=200, null=True)
    full_conversation_path = models.TextField(null=True)
    analyzed = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    objects = models.Manager()

    def __str__(self) -> str:
        return f"{'id:' + str(self.id) + ' date:' + str(self.date) + ' first_prevailing_emotion:' + str(self.first_prevailing_emotion) +' second_prevailing_emotion:' + str(self.second_prevailing_emotion) + ' analyzed:' + str(self.analyzed)}   "


class Questionnaire(models.Model):
    class Meta:
        db_table = 'questionnaire'

    emotion = models.ForeignKey("Emotion", on_delete=models.CASCADE)
    request = models.ForeignKey("Request", on_delete=models.CASCADE)
    score = models.IntegerField(null=True)
    objects = models.Manager()

    def __str__(self) -> str:
        return f"{'emotion:' +  str(self.emotion) + 'request:' + str(self.request)+ 'score:' + str(self.score)}"

class StressRecord(models.Model):
    class Meta:
        db_table = 'stress_record'

    date = models.DateField(auto_now=True)
    stressedUsers = models.IntegerField()
    company = models.ForeignKey("Company", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.date + ' stressed:' + self.stressedUsers}"

