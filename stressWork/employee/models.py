from django.db import models


class Employee(models.Model):
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    birthday = models.DateField()
    stressed = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.name + self.surname}"


class Emotions(models.Model):
    emotion_name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.emotion_name}"


class ChatSession(models.Model):
    employee_id = models.ForeignKey("Employee", on_delete=models.CASCADE)
    date = models.DateTimeField()
    first_prevailing_emotion = models.ForeignKey("Emotions", related_name="first_prevailing_emotion",
                                                 on_delete=models.DO_NOTHING)
    second_prevailing_emotion = models.ForeignKey("Emotions", related_name="second_prevailing_emotion",
                                                  on_delete=models.DO_NOTHING)
    full_video_path = models.CharField(max_length=50)
    full_audio_path = models.CharField(max_length=50)
    full_conversation_path = models.TextField()

    def __str__(self) -> str:
        return f"{self.employee_id + ' date:' + self.date}"


class ChatSessionMessage(models.Model):
    session_id = models.ForeignKey("ChatSession", on_delete=models.CASCADE)
    date = models.DateTimeField()
    video_url = models.CharField(max_length=50)
    audio_url = models.CharField(max_length=50)
    text = models.TextField()
    chatbot_answer = models.TextField()

    def __str__(self) -> str:
        return f"{self.session_id + ' date:' + self.date}"


class StressRecord(models.Model):
    date = models.DateField(auto_now=True)
    stressedUsers = models.IntegerField()

    def __str__(self):
        return f"{self.date + ' stressed:' + self.stressedUsers}"
