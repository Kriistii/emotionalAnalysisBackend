import openai
import random
import re
from ..models import EmployeeTopic, Topic
from ..serializers import TopicSerializer, EmployeeTopicSerializer
from asgiref.sync import sync_to_async

openai.api_key = "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"
completion = openai.Completion()

start_sequence = "\nCloudia:"
restart_sequence = "\n\nHuman:"
start_message = "Cloudia: Hello, Alessio I am Cloudia, the first bot that will make you talk during work hours!"
start_chat_log = "Cloudia: Hello, Alessio I am Cloudia, the first bot that will make you talk during work hours!\n\nHuman: What i can do with you?\nCloudia: You can ask me questions, we can talk about a lot of things. Why don't you tell me how the day went?\n\nHuman: How many times i can talk with you?\nCloudia: You can talk with me how many times you want, but you will receive a reward only for the first two times.\n\nHuman: What i need to do in order to obtain the reward?\nCloudia: You need to talk with me for at least 10 minutes, it wont be hard, i hope."
start_fsession_message = "Cloudia: Hello, Alessio I am Cloudia, the first bot that will make you talk during work hours! By talking with me you'll get some rewards, also you'll help your company to build the best possible enviroment to work on! In fact every data collected will be used by your employers to improve the life quality at the company, so don't worry, you can share everything with me!"
start_chat_lol_fsession = "Cloudia: Hello, Alessio I am Cloudia, the first bot that will make you talk during work hours! By talking with me you'll get some rewards, also you'll help your company to build the best possible enviroment to work on! In fact every data collected will be used by your employers to improve the life quality at the company, so don't worry, you can share everything with me!\n\nHuman: What you are used to?\nCloudia: We will talk together about everything, later your data can be seen only by your employer\n\nHuman: What i get by talking with you?\nCloudia: By talking with me for 3 minutes you'll earn a coin. Later you can spend the coin to speel the wheel and win some prizes!\n\nHuman: How many times can i talk to you?\nCloudia: You can talk with me as many times as you like, but you'll earn the coins only twice every day."

restart_conversation_phrase = ["I am sorry but I didn't understand. By the way, let's change topic! ",
                               "Oh, I think i didn't understand what you mean, but it is fine, we can talk about it later. Let's change subject for the moment! "]


async def ask(question, employee_id, session, chat_log=None,):
    prompt_text = f'{chat_log}{restart_sequence}:{question}{start_sequence}:'
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt_text,
        temperature=0.8,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.3,
        stop=["\n"]
    )
    story = response['choices'][0]['text']

    if len(story) > 1 and '?' in story:
        return str(story)
    if len(story) <= 1 or re.search("I didn't understand", story, re.IGNORECASE):
        answer = await keep_conversation_alive(employee_id, session)
        return f'{restart_conversation_phrase[random.randint(0, len(restart_conversation_phrase) - 1)]} {answer}'
    if '?' not in story:
        question = await keep_conversation_alive(employee_id, session)
        return f"{story} Let's change topic! {question}"


def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    return f'{chat_log}{restart_sequence} {question}{start_sequence}{answer}'


@sync_to_async
def keep_conversation_alive(emp_id, session):
    employee_topics = EmployeeTopicSerializer((EmployeeTopic.objects.filter(employee=emp_id)), many=True).data
    employee_topics_id_list = []
    for emp_topic in employee_topics:
        employee_topics_id_list.append(emp_topic['topic_id'])
    topics = TopicSerializer((Topic.objects.exclude(
        id__in=employee_topics_id_list)), many=True).data
    if len(topics) > 0:
        selected_topic = topics[random.randint(0, len(topics) - 1)]
        session['topic'] = {
            'id': selected_topic['id'], 'name': selected_topic['name']}
        session['topicQuestion'] = True
        return selected_topic['start_question']
    elif len(employee_topics_id_list) > 0:
        subject = employee_topics[random.randint(0, len(employee_topics)-1)]
        answer = compute_answer(
            session, f'Ask me a question about {subject["answer"]}', emp_id)
        # TODO need to ask questions about the topics the user already replied to
        return answer


async def compute_answer(session, question, employee_id):
    chat_log = session.get('chat_log', None)
    if chat_log is None:
        chat_log = start_chat_log
    answer = await ask(question, employee_id, session, chat_log)
    session['chat_log'] = append_interaction_to_chat_log(
        question, answer, chat_log)
    # TODO save the question and the answer somewhere
    return answer
