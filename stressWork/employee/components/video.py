from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def save_video(video_file, name):
    default_storage.save(
                'tmp/videos/{}.webm'.format(name), ContentFile(video_file.read()))