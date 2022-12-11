import text2emotion as te
from asgiref.sync import sync_to_async
from nltk.sentiment import SentimentIntensityAnalyzer
from ..models import ChatSessionMessage, ChatSession
import nltk
import json
from datetime import datetime
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

