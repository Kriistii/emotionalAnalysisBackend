import openai

openai.api_key = "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"
completion = openai.Completion()

start_sequence = "\nCloudia:"
restart_sequence = "\n\nHuman:"
start_chat_log = "Human: Hello, I am Alessio\nCloudia: Hello, Alessio I am Cloudia, the first bot that will make you talk during work hours!\n\nHuman: What i can do with you?\nCloudia: You can ask me questions, we can talk about a lot of things. Why don't you tell me how the day went?\n\nHuman: How many times i can talk with you?\nCloudia: You can talk with me how many times you want, but you will receive a reward only for the first two times.\n\nHuman: What i need to do in order to obtain the reward?\nCloudia: You need to talk with me for at least 10 minutes, it wont be hard, i hope."


def ask(question, chat_log=None):
    prompt_text = f'{chat_log}{restart_sequence}:{question}{start_sequence}:'
    response = openai.Completion.create(
        engine="davinci",
        prompt=prompt_text,
        temperature=0.8,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.3,
        stop=["\n"]
    )
    story = response['choices'][0]['text']
    return str(story)


def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    return f'{chat_log}{restart_sequence} {question}{start_sequence}{answer}'

def compute_answer(request, question):
    chat_log = request.session.get('chat_log', None)
    if chat_log is None:
        chat_log = start_chat_log
    answer = ask(question, chat_log)
    request.session['chat_log'] = append_interaction_to_chat_log(
        question, answer, chat_log)
    print(request.session.get('chat_log'))
    # TODO save the question and the answer somewhere
    return answer