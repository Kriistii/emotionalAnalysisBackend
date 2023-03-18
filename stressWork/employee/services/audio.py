from django.core.files.storage import default_storage
import speech_recognition as sr
import moviepy.editor as mp
from transformers import AutoConfig, Wav2Vec2Processor
import torchaudio
import torch.nn as nn
import torch.nn.functional as F
import torch
import pandas as pd
from transformers.models.wav2vec2.modeling_wav2vec2 import (
    Wav2Vec2PreTrainedModel,
    Wav2Vec2Model
)
from torch.nn import BCEWithLogitsLoss, CrossEntropyLoss, MSELoss
from typing import Optional, Tuple
from transformers.file_utils import ModelOutput
from dataclasses import dataclass
import os
from ..utilityFunctions import safe_open
from moviepy.editor import *
import environ

env = environ.Env()

def speech_to_text(session_id, identifier):
    audio_path = default_storage.path("tmp/{}/audios/{}.wav".format(session_id, identifier))
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
        return text.lower()


def video_to_audio(session_id, identifier):
    video_path = default_storage.path("tmp/{}/videos/{}.webm".format(session_id, identifier))
    clip = mp.VideoFileClip(r'{}'.format(video_path))
    path = f'tmp/{session_id}/audios/{identifier}.wav'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    clip.audio.write_audiofile(path, codec='pcm_s16le', ffmpeg_params=["-ac", "1", "-ar", "44100"])

    return path


def save_audio(session_id, audio_file, name):
    path = "tmp/{}/audios/{}.wav".format(session_id, name)
    with safe_open(path, 'wb') as binary_file:
        binary_file.write(audio_file)
    return path


def analyze_audio(audio_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_name_or_path = env('MODEL_PATH')
    config = AutoConfig.from_pretrained(
        model_name_or_path, local_files_only=True)
    processor = Wav2Vec2Processor.from_pretrained(
        model_name_or_path, local_files_only=True)
    model = Wav2Vec2ForSpeechClassification.from_pretrained(
        model_name_or_path, local_files_only=True).to(device)

    def speech_file_to_array_fn(path, sampling_rate):
        speech_array, _sampling_rate = torchaudio.load(path)
        resampler = torchaudio.transforms.Resample(_sampling_rate)
        speech = resampler(speech_array).squeeze().numpy()
        return speech

    def predict(path, sampling_rate):
        speech = speech_file_to_array_fn(path, sampling_rate)
        features = processor(speech, sampling_rate=sampling_rate, return_tensors="pt", padding=True)
        input_values = features.input_values.to(device)
        attention_mask = features.attention_mask.to(device)
        with torch.no_grad():
            logits = model(input_values, attention_mask=attention_mask).logits
        scores = F.softmax(logits, dim=1).detach().cpu().numpy()[0]
        outputs = [{"Emotion": config.id2label[i], "Score": f"{round(score * 100, 3):.1f}"} for i, score in
                   enumerate(scores)]
        return outputs

    def prediction(path):
        outputs = predict(path, 16000)
        r = pd.DataFrame(outputs)
        r = r.astype({'Score': 'float'})
        r.sort_values(['Score'], ascending=False, inplace=True)
        dict_emotions = dict(zip(r['Emotion'], r['Score']))
        filtered_emotion_dict = {'sd': dict_emotions['sd'], 'an': dict_emotions['an'], 'fr': dict_emotions['fr'], 'hp': dict_emotions['hp'],
                      'sr': dict_emotions['sr']}
        return filtered_emotion_dict

    result = prediction(audio_path)
    return result


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


'''
def mergeAndAnalyzeAudio(chat_session_id):
    messages = ChatSessionMessageSerializer(
        ChatSessionMessage.objects.filter(session=ChatSession(pk=chat_session_id)).order_by('date'), many=True).data
    if len(messages):
        audios = []
        for message in messages:
            if message['audio_url'] is not None:
                audios.append(AudioFileClip(message['audio_url']))
        if len(audios):
            final = concatenate_audioclips(audios)
            path = 'tmp/{}/full_audio.wav'.format(chat_session_id)
            final.write_audiofile(path, codec='pcm_s16le', ffmpeg_params=["-ac", "1", "-ar", "44100"])

            chat_session = ChatSession.objects.get(pk=chat_session_id)
            chat_session.full_audio_path = path
            chat_session.save()

            analysis_results = analyze_audio(path)

            return analysis_results
    else:
        return None
'''