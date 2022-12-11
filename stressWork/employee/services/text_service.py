import text2emotion as te
from asgiref.sync import sync_to_async
from nltk.sentiment import SentimentIntensityAnalyzer
from ..models import ChatSessionMessage, ChatSession
from ..serializers import ChatSessionMessageSerializer
import nltk
import json
from asgiref.sync import sync_to_async
import os

nltk.download('vader_lexicon')
nltk.download('omw-1.4')


def safe_open_w(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, 'w')


def analyzeText(text):
    sia = SentimentIntensityAnalyzer()
    print(text)
    compound = sia.polarity_scores(text)["compound"]
    print("Positive") if compound >= 0 else print("Negative")
    print(te.get_emotion(text))

    return compound


@sync_to_async
def mergeText(chat_session_id):
    session_messages = ChatSessionMessage.objects.filter(session=ChatSession(pk=chat_session_id)).order_by("date")
    print(session_messages)
    if len(session_messages):
        conversation = []
        for message in session_messages:
            conversation.append({"from": "User", "text": message.text})
            conversation.append({"from": "Chatbot", "text": message.chatbot_answer})
        text_path = f'tmp/{chat_session_id}/chat_text.json'
        os.makedirs(os.path.dirname(text_path), exist_ok=True)
        with open(text_path, "w") as outfile:
            json.dump(conversation, outfile, ensure_ascii=False, indent=4)

        chat_session = ChatSession.objects.get(pk=chat_session_id)
        chat_session.full_conversation_path = text_path
        chat_session.save()
        return text_path
    else:
        return None



