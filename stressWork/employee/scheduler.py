import sys

from apscheduler.schedulers.background import BackgroundScheduler

from .models import Employee, StressRecord, ChatSession
from .serializers import ChatSessionSerializer
from .services import text_service, audio, video

scheduler = BackgroundScheduler()


def save_data():
    stressedEmployees = Employee.objects.filter(stressed=True).count()
    StressRecord.objects.create(stressedUsers=stressedEmployees)

def run_analysis():
    chat = ChatSession.objects.filter(analyzed=False, completed=True).order_by('date')
    chatSerialized = ChatSessionSerializer(chat, many=True).data
    if len(chatSerialized):
        chatId = chatSerialized[0]['id']
        print(chatId)
        text_analysis_results = text_service.mergeAndAnalyzeText(chatId)
        audio_analysis_results = audio.mergeAndAnalyzeAudio(chatId)
        video_analysis_results = video.mergeAndAnalyzeVideo(chatId)
        print("text")
        print(text_analysis_results)
        print("audio")
        print(audio_analysis_results)
        print("video")
        print(video_analysis_results)
        c = ChatSession.objects.get(pk=chatId)
        c.analyzed = True
        c.save()





def startScheduler():
    # run this job every 24 hours
    scheduler.add_job(run_analysis, 'interval', minutes=5, name='run_analysis', jobstore='default')
    scheduler.add_job(save_data, 'interval', hours=24, name='save_data', jobstore='default')
    scheduler.start()
    print("Scheduler started...", file=sys.stdout)
