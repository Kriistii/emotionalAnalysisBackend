from django.core.files.storage import default_storage
import speech_recognition as sr
import moviepy.editor as mp
from transformers import AutoConfig, Wav2Vec2Processor
import torchaudio
import torch.nn as nn
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
from django.core.files.base import ContentFile

def speech_to_text(identifier):
    audio_path = default_storage.path("tmp/audios/{}.wav".format(identifier))
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
        return text.lower()

def video_to_audio(identifier):
    video_path = default_storage.path("tmp/videos/{}.webm".format(identifier))
    clip = mp.VideoFileClip(r'{}'.format(video_path))
    audio_folder_path = default_storage.path("tmp/audios/")
    clip.audio.write_audiofile(f'{audio_folder_path}/{identifier}.wav',
                               codec='pcm_s16le', ffmpeg_params=["-ac", "1", "-ar", "44100"])

def save_video(audio_file, name):
    default_storage.save('tmp/audios/{}.wav'.format(name), ContentFile(audio_file.read()))


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

