from nltk.sentiment import SentimentIntensityAnalyzer
import text2emotion as te


def analyzeText(text):
    sia = SentimentIntensityAnalyzer()
    compound = sia.polarity_scores(text)["compound"]

    return compound


if __name__ == '__main__':
    print("Text elaborator:")

    while True:
        statement = input("> ")

        if statement == '':
            break

        result = analyzeText(statement)
        print("Positive") if result > 0 else print("Negative")
        print(te.get_emotion(statement))