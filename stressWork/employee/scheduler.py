import sys
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from django.db.models import Count

from .models import Employee, StressRecord, Emotion, Session, SessionResults
from .serializers import SessionSerializer
from .services import text_service, audio, video

scheduler = BackgroundScheduler()


def save_data():
    stressedEmployees = Employee.objects.filter(stressed=True)\
        .values('company_id')\
        .annotate(stressedEmployees=Count('*'))\
        .order_by()

    for entry in stressedEmployees:
        stressRecord = StressRecord(stressedUsers=entry['stressedEmployees'], company_id=entry['company_id'])
        stressRecord.save()

def save_results(session, text_results, text_results2, audio_results, video_results):
    result_text = SessionResults(session=Session(pk=session.id), text=True,
                                 happiness=text_results['hp'],  sadness=text_results['sd'],
                                 anger=text_results['an'], fear=text_results['fr'],
                                 surprise=text_results['sr'])
    result_audio = SessionResults(session=Session(pk=session.id), audio=True,
                                 happiness=audio_results['hp'],  sadness=audio_results['sd'],
                                 anger=audio_results['an'], fear=audio_results['fr'],
                                 surprise=audio_results['sr'],neutrality=audio_results['nt'])
    result_video = SessionResults(session=Session(pk=session.id), video=True,
                                 happiness=video_results['hp'],  sadness=video_results['sd'],
                                 anger=video_results['an'], fear=video_results['fr'],
                                 surprise=video_results['sr'], neutrality=video_results['nt'])
    session.text_result = text_results2[0]
    session.save()
    result_text.save()
    result_audio.save()
    result_video.save()


def run_analysis():
    #todo add company
    user_sessions = Session.objects.filter(analyzed=False, completed=True).order_by('date')

    for s in user_sessions:
        session_serialized = SessionSerializer(s).data
        text_weight = 0.333
        audio_weight = 0.333
        video_weight = 0.333

        print('running text')
        text_analysis_results = text_service.analyzeText(session_serialized['text'])
        print(text_analysis_results)
        print('running text-it')
        text_analysis_results2 = text_service.analyzeTextIt(session_serialized['text'])
        print(text_analysis_results2)

        print('running audio')
        audio_analysis_results = audio.analyze_audio(session_serialized['full_audio_path'])
        print(audio_analysis_results)

        print('running video')
        video_analysis_results = video.analyze_video(session_serialized['id'], session_serialized['full_video_path'])
        print(video_analysis_results)
        save_results(s, text_analysis_results,text_analysis_results2, audio_analysis_results, video_analysis_results)
        sum_emotions = {}
        emotions = ['sd', 'an', 'fr', 'hp', 'sr', 'nt']
        for e in emotions:
            score_text = 0
            score_video = 0
            score_audio = 0

            if text_analysis_results is not None:
                score_text = text_analysis_results[e] * text_weight
            if audio_analysis_results is not None:
                score_video = audio_analysis_results[e] * audio_weight
            if video_analysis_results is not None:
                score_video = video_analysis_results[e] * video_weight

            sum_emotions[e] = score_text + score_video + score_audio
        sum_emotions_ordered = sorted(sum_emotions.items(), key=lambda x: x[1], reverse=True)
        first_emotion = sum_emotions_ordered[0]
        second_emotion = sum_emotions_ordered[1]

        if float(first_emotion[1]) / 2 > float(second_emotion[1]):
            s.first_prevailing_emotion = Emotion.objects.get(emotion_name=first_emotion[0])
        else:
            s.first_prevailing_emotion = Emotion.objects.get(emotion_name=first_emotion[0])
            s.second_prevailing_emotion = Emotion.objects.get(emotion_name=second_emotion[0])
        s.analyzed = True
        s.save()




def stressAnalysis(employee_id):
    #Params
    minumumDays = 7
    thresholdStressPercentage = 0.7
    good_emotions = [3, 5]
    bad_emotions = [1, 2, 4]

    #Logic
    emp = Employee.objects.get(pk=employee_id)
    chats = SessionSerializer(Session.objects.filter(employee=emp, completed=True, date__range=(datetime.now() - timedelta(days=15), datetime.now())).order_by('-date'), many=True).data
    analyzed_dates = []
    for c in chats:
        date = datetime.strptime(c['date'], '%Y-%m-%dT%H:%M:%S.%fZ').date()
        if date not in analyzed_dates:
            analyzed_dates.append(date)
    if len(analyzed_dates) < minumumDays:
        emp.firstSession = True
        emp.save()
        return
    else:
        score_positive = 0
        score_negative = 0

        for ch in chats:
            if ch['first_prevailing_emotion'] in good_emotions:
                score_positive = score_positive + 1
            elif ch['first_prevailing_emotion'] in bad_emotions:
                score_negative = score_negative + 1
            if ch['second_prevailing_emotion'] in good_emotions:
                score_positive = score_positive + 0.5
            elif ch['second_prevailing_emotion'] in bad_emotions:
                score_negative = score_negative + 0.5

        negativePercentage = score_negative / (score_positive + score_negative)

        emp.firstSession = True

        if negativePercentage >= thresholdStressPercentage:
            emp.stressed = True
        else:
            emp.stressed = False

        emp.save()
        return

def startScheduler():
    # run this job every 24 hours
    scheduler.add_job(run_analysis, 'interval', minutes=15, name='run_analysis', jobstore='default')
   # scheduler.add_job(save_data, 'interval', hours=24, name='save_data', jobstore='default')
    scheduler.start()
    print("Scheduler started...", file=sys.stdout)
