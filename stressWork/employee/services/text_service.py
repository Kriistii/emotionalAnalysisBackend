import text2emotion as te
import pandas as pd
from ..models import ChatSessionMessage, ChatSession
import json
from asgiref.sync import sync_to_async
import os




def safe_open_w(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, 'w')


def analyzeText(text):
    r = pd.DataFrame.from_dict(te.get_emotion(text), orient='index')
    r.sort_values(r.columns[0], ascending=False, inplace=True)
    return r.iloc[:2]



@sync_to_async
def mergeAndAnalyzeText(chat_session_id):
    session_messages = ChatSessionMessage.objects.filter(session=ChatSession(pk=chat_session_id)).order_by("date")
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



