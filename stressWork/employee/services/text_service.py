import text2emotion as te
import pandas as pd
import json
from asgiref.sync import sync_to_async
import os


from datetime import datetime
from mtranslate import translate
from feel_it import EmotionClassifier




def safe_open_w(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, 'w')


def analyzeText(text):
    text = translate(text, 'en', 'auto')
    r = pd.DataFrame.from_dict(te.get_emotion(text), orient='index')
    r.sort_values(r.columns[0], ascending=False, inplace=True)
    dictionary = r[0].to_dict()
    emotions_score = {'sd': dictionary['Sad']*100, 'an': dictionary['Angry']*100, 'fr': dictionary['Fear']*100, 'hp': dictionary['Happy']*100,
                      'sr': dictionary['Surprise']*100, 'nt' : 0}

    return emotions_score

def analyzeTextIt(text):
    emotion_classifier = EmotionClassifier()
    print(text)
    emotions = emotion_classifier.predict([text])
    print(emotions)
    return emotions
'''
def mergeAndAnalyzeText(text):
    session_messages = ChatSessionMessage.objects.filter(session=ChatSession(pk=chat_session_id)).order_by("date")
    if len(session_messages):
        conversation = []
        for message in session_messages:
            conversation.append({"from": "User", "text": message.text, "timestamp": str(message.date) })
            conversation.append({"from": "Chatbot", "text": message.chatbot_answer, "timestamp": str(message.date)})
        text_path = f'tmp/{chat_session_id}/chat_text.json'
        os.makedirs(os.path.dirname(text_path), exist_ok=True)
        with open(text_path, "w") as outfile:
            json.dump(conversation, outfile, ensure_ascii=False, indent=4)

        chat_session = ChatSession.objects.get(pk=chat_session_id)
        chat_session.full_conversation_path = text_path
        chat_session.save()

        stringToAnalyze = ''
        for m in conversation:
            if m['from'] == 'User':
                if len(stringToAnalyze) == 0:
                    stringToAnalyze += m['text']
                else:
                    stringToAnalyze += '. ' + m['text']
        if len(stringToAnalyze):
            analysis_result = analyzeText(stringToAnalyze)
            return analysis_result
        else:
            return None
    else:
        return None
'''


