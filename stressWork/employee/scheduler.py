import sys

from apscheduler.schedulers.background import BackgroundScheduler

from .models import Employee, StressRecord, ChatSession, Emotion
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
        weigthText = 0.333
        weigthAudio = 0.333
        weigthVideo = 0.333
        chatId = chatSerialized[0]['id']
        print(chatId)
        text_analysis_results = text_service.mergeAndAnalyzeText(chatId)
        audio_analysis_results = audio.mergeAndAnalyzeAudio(chatId)
        video_analysis_results = video.mergeAndAnalyzeVideo(chatId)
        sum_emotions = {}
        emotions = ['sd', 'an', 'fr', 'hp', 'sr']
        for e in emotions:
            score_text = 0
            score_video = 0
            score_audio = 0

            if text_analysis_results is not None:
                score_text = text_analysis_results[e] * weigthText
            if audio_analysis_results is not None:
                score_video = audio_analysis_results[e] * weigthAudio
            if video_analysis_results is not None:
                score_video = video_analysis_results[e] * weigthVideo

            sum_emotions[e] = score_text + score_video + score_audio
        sum_emotions_ordered = sorted(sum_emotions.items(), key=lambda x: x[1], reverse=True)
        print("result")
        first_emotion = sum_emotions_ordered[0]
        second_emotion = sum_emotions_ordered[1]
        c = ChatSession.objects.get(pk=chatId)

        if float(first_emotion[1]) / 2 > float(second_emotion[1]):
            c.first_prevailing_emotion = Emotion.objects.get(emotion_name=first_emotion[0])
        else:
            c.first_prevailing_emotion = Emotion.objects.get(emotion_name=first_emotion[0])
            c.second_prevailing_emotion = Emotion.objects.get(emotion_name=second_emotion[0])
        c.analyzed = True
        c.save()
        #TODO save result and don't save the second emotion if its not at least half (Or just not save it at all)


def startScheduler():
    # run this job every 24 hours
    scheduler.add_job(run_analysis, 'interval', minutes=1, name='run_analysis', jobstore='default')
    scheduler.add_job(save_data, 'interval', hours=24, name='save_data', jobstore='default')
    scheduler.start()
    print("Scheduler started...", file=sys.stdout)
