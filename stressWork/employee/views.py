import uuid
import os

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import speech_recognition as sr
import openai

from transformers import AutoConfig, Wav2Vec2Processor
from transformers.models.wav2vec2.modeling_wav2vec2 import (
    Wav2Vec2PreTrainedModel,
    Wav2Vec2Model
)
from sklearn.metrics import classification_report, confusion_matrix
from datasets import load_dataset, load_metric
from torch import nn
import moviepy.editor as mp
import torch
import torchaudio
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sn

from .models import Employee
from .serializers import EmployeeSerializer

openai.api_key = "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"
completion = openai.Completion()

start_sequence = "\nAI:"
restart_sequence = "\n\nHuman:"
start_chat_log = "Human: Hello, I am Alessio\nAI: Hello, Alessio I am Pluto, the first bot that will make you talk during work hours!\n\nHuman: What i can do with you?\nAI: You can ask me questions, we can talk about a lot of things. Why don't you tell me how the day went?\n\nHuman: How many times i can talk with you?\nAI: You can talk with me how many times you want, but you will receive a reward only for the first two times.\n\nHuman: What i need to do in order to obtain the reward?\nAI: You need to talk with me for at least 10 minutes, it wont be hard, i hope."

def video(identifier):
    video_path = default_storage.path('tmp/videos/{}.webm'.format(identifier))

def audio(identifier):
    clip = mp.VideoFileClip(r'{}'.format(video_path))
    clip.audio.write_audiofile(r'/Users/alessioferrara/git/stressWorkBack/stressWork/tmp/audios/{}.wav'.format(name),codec='pcm_s16le')
    audio_path = default_storage.path("tmp/audios/{}.wav".format(name))
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language="it-IT")
        return text.lower()
        
    



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
    print(story)
    return str(story)

def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None: chat_log = start_chat_log 
    return f'{chat_log}{restart_sequence} {question}{start_sequence}{answer}'

def chatbot(request, question): 
    chat_log = request.session.get('chat_log', None)
    if chat_log is None: chat_log = start_chat_log 
    answer = ask(question, chat_log)
    request.session['chat_log'] = append_interaction_to_chat_log(question, answer, chat_log)
    print(request.session.get('chat_log'))
    #TODO save the question and the answer somewhere
    return answer


class Wav2Vec2ClassificationHead(nn.Module):
    def __init__(self, config):        
        super().__init__()
        self.config = config
        self.relu=nn.ReLU()
        self.out_proj = nn.Linear(config.hidden_size, config.num_labels)

    def forward(self, features, **kwargs):
        x = features
        x = self.relu(x)
        x = self.out_proj(x)
        return x

class Wav2Vec2ForSpeechClassification(Wav2Vec2PreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels
        self.pooling_mode = config.pooling_mode
        self.config = config

        self.wav2vec2 = Wav2Vec2Model(config)
        self.classifier = Wav2Vec2ClassificationHead(config)

        self.init_weights()

    def freeze_feature_extractor(self):
        self.wav2vec2.feature_extractor._freeze_parameters()

    def merged_strategy(
            self,
            hidden_states,
            mode="mean"
    ):
        if mode == "mean":
            outputs = torch.mean(hidden_states, dim=1)
        elif mode == "sum":
            outputs = torch.sum(hidden_states, dim=1)
        elif mode == "max":
            outputs = torch.max(hidden_states, dim=1)[0]
        else:
            raise Exception(
                "The pooling method hasn't been defined! Your pooling mode must be one of these ['mean', 'sum', 'max']")

        return outputs

class EmployeeStatsAPIView(APIView):
    def get(self, request):
        numEmployees = Employee.objects.count()
        stressedEmployees = 0 # Employee.objects.filter(stressed=True).count()

        return Response({
            "numEmployees": numEmployees,
            "stressedEmployees": stressedEmployees
        })


class EmployeeAPIView(APIView):

    def get(self, request):
        employee = Employee.objects.all()
        item = self.request.query_params.get("item", "")

        if item != "":
            employee = employee.filter(name=item)

        serializer = EmployeeSerializer(employee, many=True)

        return Response(serializer.data)

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeDetailAPIView(APIView):

    def get(self, request, employee_id):
        employee = get_object_or_404(Employee, id=employee_id)
        serializer = EmployeeSerializer(employee)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class NewRecordAPIView(APIView):
    def post(self, request):
        print(request.session.get('chat_log'))
        video_file = request.FILES['video-blob']
        name = uuid.uuid4()
        default_storage.save('tmp/videos/{}.webm'.format(name), ContentFile(video_file.read()))
        
        #TODO At the moment we have it in case we want to do elaboration in real time, otherwise we can remove this function
        video(name)
        #We retrieve audio from the video, we save it and then we do speech to text in order to have the text to provide to the chatbot
        text = audio(name)
        #We use the text we retrieved to give to the chatbot and get an answer from him, in order to return it to the user
        bot_answer = chatbot(request, text)

        return Response(bot_answer)

        '''
        model_path = '/Users/alessioferrara/git/stressWorkBack/stressWork/content/model/pretrained-model'
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Device: {device}")
        config = AutoConfig.from_pretrained(model_path, local_files_only=True)
        processor = Wav2Vec2Processor.from_pretrained(model_path, local_files_only=True)
        target_sampling_rate = processor.feature_extractor.sampling_rate
        model = Wav2Vec2ForSpeechClassification.from_pretrained(model_path, local_files_only=True).to(device)
        test_dataset = load_dataset("csv", data_files={"test": '/Users/alessioferrara/git/stressWorkBack/stressWork/' +"test.csv"}, delimiter="\t")["test"]

        def speech_file_to_array_fn(path):
            speech_array, sampling_rate = torchaudio.load(path)
            resampler = torchaudio.transforms.Resample(sampling_rate, target_sampling_rate)
            speech = resampler(speech_array).squeeze().numpy()
            CUT = 4 # custom cut at 4 seconds for speeding up the data processing (not necessary)
            if len(speech) > 16000*CUT:
                return speech[:int(16000*CUT)]
            return speech


        def predict(batch):
            features = processor(batch["speech"], sampling_rate=processor.feature_extractor.sampling_rate, return_tensors="pt", padding=True)

            input_values = features.input_values.to(device)
            attention_mask = features.attention_mask.to(device)

            with torch.no_grad():
                logits = model(input_values, attention_mask=attention_mask).logits 

            pred_ids = torch.argmax(logits, dim=-1).detach().cpu().numpy()
            batch["predicted"] = pred_ids
            return batch

        test_dataset = test_dataset.map(speech_file_to_array_fn)
        result = test_dataset.map(predict, batched=True, batch_size=8)
        label_names = [config.id2label[i] for i in range(config.num_labels)]
        y_true = [config.label2id[name] for name in result["emotion"]]
        y_pred = result["predicted"]
        classification_report(y_true, y_pred, target_names=label_names)
        emotions = label_names
        cm=confusion_matrix(y_true, y_pred)

        df_cm = pd.DataFrame(cm.astype('float') / cm.sum(axis=1), index = [i for i in emotions],
                        columns = [i for i in emotions])
        l = 16
        fig, ax = plt.subplots(figsize=(l,l/2))
        sn.heatmap(df_cm, annot=True, cmap="coolwarm")
        ax.set(xlabel='Recognized emotion', ylabel='Expressed emotion')
        ax.xaxis.label.set_size(20)
        ax.yaxis.label.set_size(20)

        # We change the fontsize of minor ticks label 
        ax.tick_params(axis='both', which='major', labelsize=12)
        ax.tick_params(axis='both', which='minor', labelsize=12)

        plt.show()

    
        
        #TODO handle blob data and pass it to the varius analyzer
        # Build the Face detection detector
        
        location_videofile = "tmp/prova.mp4"
        face_detector = FER(mtcnn=True)
        # Input the video for processing
        input_video = Video(location_videofile)

        # The Analyze() function will run analysis on every frame of the input video. 
        # It will create a rectangular box around every image and show the emotion values next to that.
        # Finally, the method will publish a new video that will have a box around the face of the human with live emotion values.
        processing_data = input_video.analyze(face_detector, display=False, save_frames=False, save_video=False, frequency=2)

        # We will now convert the analysed information into a dataframe.
        # This will help us import the data as a .CSV file to perform analysis over it later
        vid_df = input_video.to_pandas(processing_data)
        vid_df = input_video.get_first_face(vid_df)
        vid_df = input_video.get_emotions(vid_df)

        # We will now work on the dataframe to extract which emotion was prominent in the video
        angry = sum(vid_df.angry)
        disgust = sum(vid_df.disgust)
        fear = sum(vid_df.fear)
        happy = sum(vid_df.happy)
        sad = sum(vid_df.sad)
        surprise = sum(vid_df.surprise)
        neutral = sum(vid_df.neutral)

        emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        emotions_values = [angry, disgust, fear, happy, sad, surprise, neutral]

        score_comparisons = pd.DataFrame(emotions, columns = ['Human Emotions'])
        score_comparisons['Emotion Value from the Video'] = emotions_values
        print(score_comparisons)
        '''
        
        
        
