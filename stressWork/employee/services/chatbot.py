import openai
import random
from ..models import EmployeeTopic, Topic
from ..serializers import TopicSerializer, EmployeeTopicSerializer

openai.api_key = "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"
completion = openai.Completion()

start_sequence = "\nCloudia:"
restart_sequence = "\n\nHuman:"
start_chat_log = "Human: Hello, I am Alessio\nCloudia: Hello, Alessio I am Cloudia, the first bot that will make you talk during work hours!\n\nHuman: What i can do with you?\nCloudia: You can ask me questions, we can talk about a lot of things. Why don't you tell me how the day went?\n\nHuman: How many times i can talk with you?\nCloudia: You can talk with me how many times you want, but you will receive a reward only for the first two times.\n\nHuman: What i need to do in order to obtain the reward?\nCloudia: You need to talk with me for at least 10 minutes, it wont be hard, i hope."


def ask(question, employee_id, request, chat_log=None, ):
    prompt_text = f'{chat_log}{restart_sequence}:{question}{start_sequence}:'
    response = openai.Completion.create(
        model="text-davinci-002",
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
    if len(story) <= 1:
        answer = keep_conversation_alive(employee_id, request)
        return answer
    if '?' not in story:
        question = keep_conversation_alive(employee_id, request)
        return f'{story} {question}'



def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    return f'{chat_log}{restart_sequence} {question}{start_sequence}{answer}'


def keep_conversation_alive(emp_id, request):
    employee_topics = EmployeeTopicSerializer(EmployeeTopic.objects.filter(employee=emp_id), many=True).data
    employee_topics_id_list = []
    for emp_topic in employee_topics:
        employee_topics_id_list.append(emp_topic['topic_id'])
    topics = TopicSerializer(Topic.objects.exclude(id__in=employee_topics_id_list), many=True).data
    if len(topics) > 0:
        selected_topic = topics[random.randint(0, len(topics) - 1)]
        request.session['topic'] = {'id': selected_topic['id'], 'name': selected_topic['name'] }
        request.session['topicQuestion'] = True
        return selected_topic['start_question']
    elif len(employee_topics_id_list) > 0:
        subject = employee_topics[random.randint(0, len(employee_topics)-1)]
        answer = compute_answer(request, f'Ask me a question about {subject}', emp_id)
        #TODO need to ask questions about the topics the user already replied to
        return answer
    
    



def compute_answer(request, question, employee_id):
    chat_log = request.session.get('chat_log', None)
    if chat_log is None:
        chat_log = start_chat_log
    answer = ask(question, employee_id, request, chat_log)
    request.session['chat_log'] = append_interaction_to_chat_log(
        question, answer, chat_log)
    # TODO save the question and the answer somewhere
    return answer
