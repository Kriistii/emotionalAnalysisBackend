from .serializers import EmployeeSerializer
from .models import Employee
import librosa
from transformers.models.wav2vec2.modeling_wav2vec2 import (
    Wav2Vec2PreTrainedModel,
    Wav2Vec2Model
)
from torch.nn import BCEWithLogitsLoss, CrossEntropyLoss, MSELoss
import pandas as pd
import numpy as np
from transformers import AutoConfig, Wav2Vec2Processor
import torchaudio
import torch.nn.functional as F
import torch.nn as nn
import torch
from transformers.file_utils import ModelOutput
from typing import Optional, Tuple
from dataclasses import dataclass
import text2emotion as te
from nltk.sentiment import SentimentIntensityAnalyzer
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
import moviepy.editor as mp
import nltk
nltk.download('vader_lexicon')
nltk.download('omw-1.4')

# Text analysis

# Audio analysis


openai.api_key = "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"
completion = openai.Completion()

start_sequence = "\nCloudia:"
restart_sequence = "\n\nHuman:"
start_chat_log = "Human: Hello, I am Alessio\nCloudia: Hello, Alessio I am Cloudia, the first bot that will make you talk during work hours!\n\nHuman: What i can do with you?\nCloudia: You can ask me questions, we can talk about a lot of things. Why don't you tell me how the day went?\n\nHuman: How many times i can talk with you?\nCloudia: You can talk with me how many times you want, but you will receive a reward only for the first two times.\n\nHuman: What i need to do in order to obtain the reward?\nCloudia: You need to talk with me for at least 10 minutes, it wont be hard, i hope."


def analyzeText(text):
    sia = SentimentIntensityAnalyzer()
    print(text)
    compound = sia.polarity_scores(text)["compound"]
    print("Positive") if compound > 0 else print("Negative")
    print(te.get_emotion(text))

    return compound


@dataclass
class SpeechClassifierOutput(ModelOutput):
    loss: Optional[torch.FloatTensor] = None
    logits: torch.FloatTensor = None
    hidden_states: Optional[Tuple[torch.FloatTensor]] = None
    attentions: Optional[Tuple[torch.FloatTensor]] = None


class Wav2Vec2ClassificationHead(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.relu = nn.ReLU()
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

    def forward(
            self,
            input_values,
            attention_mask=None,
            output_attentions=None,
            output_hidden_states=None,
            return_dict=None,
            labels=None,
    ):
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict
        outputs = self.wav2vec2(
            input_values,
            attention_mask=attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        hidden_states = outputs[0]
        hidden_states = self.merged_strategy(
            hidden_states, mode=self.pooling_mode)
        logits = self.classifier(hidden_states)

        loss = None
        if labels is not None:
            if self.config.problem_type is None:
                if self.num_labels == 1:
                    self.config.problem_type = "regression"
                elif self.num_labels > 1 and (labels.dtype == torch.long or labels.dtype == torch.int):
                    self.config.problem_type = "single_label_classification"
                else:
                    self.config.problem_type = "multi_label_classification"

            if self.config.problem_type == "regression":
                loss_fct = MSELoss()
                loss = loss_fct(logits.view(-1, self.num_labels), labels)
            elif self.config.problem_type == "single_label_classification":
                loss_fct = CrossEntropyLoss()
                loss = loss_fct(
                    logits.view(-1, self.num_labels), labels.view(-1))
            elif self.config.problem_type == "multi_label_classification":
                loss_fct = BCEWithLogitsLoss()
                loss = loss_fct(logits, labels)

        if not return_dict:
            output = (logits,) + outputs[2:]
            return ((loss,) + output) if loss is not None else output

        return SpeechClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )


def video(identifier):
    video_path = default_storage.path('tmp/videos/{}.webm'.format(identifier))


def analyze_audio(audio_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_name_or_path = default_storage.path('content/model/pretrained-model')
    config = AutoConfig.from_pretrained(
        model_name_or_path, local_files_only=True)
    processor = Wav2Vec2Processor.from_pretrained(
        model_name_or_path, local_files_only=True)
    sampling_rate = processor.feature_extractor.sampling_rate
    model = Wav2Vec2ForSpeechClassification.from_pretrained(
        model_name_or_path, local_files_only=True).to(device)

    def speech_file_to_array_fn(path, sampling_rate):
        speech_array, _sampling_rate = torchaudio.load(path)
        resampler = torchaudio.transforms.Resample(
            _sampling_rate, sampling_rate)
        speech = resampler(speech_array).squeeze().numpy()
        # custom cut at 4 seconds for speeding up the data processing (not necessary)
        CUT = 4
        if len(speech) > 16000*CUT:
            return speech[:int(16000*CUT)]
        return speech

    def predict(path, sampling_rate):
        speech = speech_file_to_array_fn(path, sampling_rate)
        features = processor(
            speech, sampling_rate=processor.feature_extractor.sampling_rate, return_tensors="pt", padding=True)

        input_values = features.input_values.to(device)
        attention_mask = features.attention_mask.to(device)

        with torch.no_grad():
            logits = model(input_values, attention_mask=attention_mask).logits

        scores = torch.argmax(logits, dim=-1).detach().cpu().numpy()
        outputs = [{"Emotion": config.id2label[i],
                    "Score": f"{round(score * 100, 3):.1f}%"} for i, score in enumerate(scores)]
        return outputs

    def prediction(path):
        outputs = predict(path, sampling_rate)
        print(outputs)
        r = pd.DataFrame(outputs)
        print(r.to_string())

    prediction(audio_path)


def audio(identifier, video_path):

    clip = mp.VideoFileClip(r'{}'.format(video_path))
    audio_folder_path = default_storage.path("tmp/audios/")
    clip.audio.write_audiofile(f'{audio_folder_path}/{identifier}.wav',
                               codec='pcm_s16le', ffmpeg_params=["-ac", "1", "-ar", "44100"])
    audio_path = default_storage.path("tmp/audios/{}.wav".format(identifier))
    analyze_audio(audio_path)

    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
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
    return str(story)


def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = start_chat_log
    return f'{chat_log}{restart_sequence} {question}{start_sequence}{answer}'


def chatbot(request, question):
    chat_log = request.session.get('chat_log', None)
    if chat_log is None:
        chat_log = start_chat_log
    answer = ask(question, chat_log)
    request.session['chat_log'] = append_interaction_to_chat_log(
        question, answer, chat_log)
    print(request.session.get('chat_log'))
    # TODO save the question and the answer somewhere
    return answer


class EmployeeStatsAPIView(APIView):
    def get(self, request):
        numEmployees = Employee.objects.count()
        stressedEmployees = 0  # Employee.objects.filter(stressed=True).count()

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
        if request.FILES.get('video-blob', None):
            video_file = request.FILES['video-blob']
            name = uuid.uuid4()
            default_storage.save(
                'tmp/videos/{}.webm'.format(name), ContentFile(video_file.read()))
            # We elaborate the audio with OpenFace
            video(name)
            # We retrieve audio from the video, we save it and then we do speech to text in order to have the text to provide to the chatbot
            text = audio(name, default_storage.path(
                'tmp/videos/{}.webm').format(name))
            analyzeText(text)
        if request.FILES.get('audio-blob', None):
            #TODO implement logic for audio-blob only
            print(request.FILES['audio-blob'])

        if request.POST.get('text', None):
            text = request.POST['text']
            analyzeText(text)
            answer = chatbot(request, text)
            return Response(answer)
        # TODO At the moment we have it in case we want to do elaboration in real time, otherwise we can remove this function

        # We use the text we retrieved to give to the chatbot and get an answer from him, in order to return it to the user
        #bot_answer = chatbot(request, text)

        return Response("ok")
