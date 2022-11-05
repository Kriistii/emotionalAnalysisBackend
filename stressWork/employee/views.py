from fer import Video
from fer import FER
import os
import sys
import pandas as pd

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Employee, Record
from .serializers import EmployeeSerializer, RecordSerializer


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
        print(request.body)
        #TODO handle blob data and pass it to the varius analyzer
        # Build the Face detection detector
        face_detector = FER(mtcnn=True)
        # Input the video for processing
        input_video = Video(location_videofile)

        # The Analyze() function will run analysis on every frame of the input video. 
        # It will create a rectangular box around every image and show the emotion values next to that.
        # Finally, the method will publish a new video that will have a box around the face of the human with live emotion values.
        processing_data = input_video.analyze(face_detector, display=False)

        # We will now convert the analysed information into a dataframe.
        # This will help us import the data as a .CSV file to perform analysis over it later
        vid_df = input_video.to_pandas(processing_data)
        vid_df = input_video.get_first_face(vid_df)
        vid_df = input_video.get_emotions(vid_df)

        # Plotting the emotions against time in the video
        pltfig = vid_df.plot(figsize=(20, 8), fontsize=16).get_figure()

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
        score_comparisons
        return Response("Ok")
