import text2emotion as te
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

nltk.download('vader_lexicon')
nltk.download('omw-1.4')


def analyzeText(text):
    sia = SentimentIntensityAnalyzer()
    print(text)
    compound = sia.polarity_scores(text)["compound"]
    print("Positive") if compound >= 0 else print("Negative")
    print(te.get_emotion(text))

    return compound
