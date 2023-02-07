from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd
from os.path import exists

import csv
import subprocess
import cv2
import os
import shutil
from ..utilityFunctions import *
from ..models import ChatSessionMessage, ChatSession
from ..serializers import ChatSessionMessageSerializer
from moviepy.editor import *
import environ
from asgiref.sync import sync_to_async

env = environ.Env()


def mergeAndAnalyzeVideo(session_id):
    messages = ChatSessionMessageSerializer(ChatSessionMessage.objects.filter(session=ChatSession(pk=session_id)).order_by('date'), many=True).data
    if len(messages):
        videos = []
        for message in messages:
            if message['video_url'] is not None:
                videos.append(VideoFileClip(message['video_url']))
        if len(videos):
            final = concatenate_videoclips(videos)
            path = 'tmp/{}/full_video.webm'.format(session_id)
            final.write_videofile(path)

            chat_session = ChatSession.objects.get(pk=session_id)
            chat_session.full_video_path = path
            chat_session.save()
            results = analyze_video(session_id)
            return results
    else:
        return None


def save_video(session_id, video_file, name):
    path = 'tmp/{}/videos/{}.webm'.format(session_id, name)
    with safe_open(path, 'wb') as binary_file:
        binary_file.write(video_file)
    return path


def analyze_video(identifier):
    # get paths, for video processing
    video_path = default_storage.path('tmp/{}/full_video.webm'.format(identifier))
    csv_path = default_storage.path(f'tmp/{identifier}/csv')
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    openFaceExecPath = env('OPEN_FACE_EXEC_PATH')
    print(openFaceExecPath)

    video = VideoFileClip(video_path)
    duration = video.duration


    start = 0
    # create dir to store all 1s videos
    while (duration > 1):
        end = start + 1

        duration = duration - 1
        path_video = f'tmp/{identifier}/tmp_videos/{start}.webm'
        os.makedirs(os.path.dirname(path_video), exist_ok=True)
        clip = video.subclip(start, end)
        clip.write_videofile(path_video)
        # split video in 1s videos
        # run video analysis for each video
        subprocess.call(f' {openFaceExecPath} -f {path_video} -aus -out_dir {csv_path} ',
                        shell=True)

        # emotion analysis
        mostCommonUnits = csvProcessing2(identifier, start)
        emotionsPointsDataFrame = findEmotionsPerFrame2(mostCommonUnits)
        sumEmotionsAndSaveCsv(emotionsPointsDataFrame, identifier)
        start = end

    results = sessionResultsProcessing(identifier)
    # delete videos, todo delete all csvs, leave only the main one
    shutil.rmtree(default_storage.path('tmp/{}/tmp_videos'.format(identifier)))
    shutil.rmtree(default_storage.path('tmp/{}/csv'.format(identifier)))

    start = end
    return results


def csvProcessing2(session_id, csv_name):
    with open(default_storage.path('tmp/{}/csv/{}.csv'.format(session_id, csv_name))) as file:
        fullFinal = []
        headArray = []
        reader = csv.reader(file)
        columns = pd.read_csv(file).columns
        for col in columns:
            if "_r" in col:
                headArray.append()
        fullFinal.append((columns))
        for i, row in enumerate(reader):
            final = []
            if(i == 1):
                for index, element in enumerate(row):
                    # get all fu values, only the ones with probability > 0.7
                    if 5 <= index <= 21:
                        final.append(float(element))
                fullFinal.append(final)
    # full final has the best predicted fus
    return fullFinal


def findEmotionsPerFrame2(fuArrayFrames):
    # fu for emotions
    anger = ['AU04_r', 'AU05_r', 'AU07_r', 'AU10_r', 'AU17_r', 'AU22_r', 'AU23_r', 'AU24_r', 'AU25_r', 'AU26_r']
    disgust = ['AU09_r', 'AU10_r', 'AU16_r', 'AU17_r', 'AU25_r', 'AU26_r']
    fear = ['AU01_r', 'AU02_r', 'AU04_r', 'AU05_r', 'AU20_r', 'AU25_r', 'AU26_r', 'AU27_r']
    happiness = ['AU06_r', 'AU12_r', 'AU25_r']
    sadness = ['AU01_r', 'AU04_r', 'AU06_r', 'AU11_r', 'AU15_r', 'AU17_r']
    surprise = ['AU01_r', 'AU02_r', 'AU05_r', 'AU26_r', 'AU27_r']

    finalEmotionPoints = []
    angerPointsArray = []
    disgustPointsArray = []
    fearPointsArray = []
    happinessPointsArray = []
    sadnessPointsArray = []
    surprisePointsArray = []

    for index, frame in enumerate(fuArrayFrames):
        angerPoints = 0
        disgustPoints = 0
        fearPoints = 0
        happinessPoints = 0
        sadnessPoints = 0
        surprisePoints = 0

        if (index == 0):
            continue

        # if face unit of frame, is found on emotion set, add 1 to its score
        for index2, faceUnitValue in enumerate(frame):
            if fuArrayFrames[0][index2] in anger:
                angerPoints = angerPoints + faceUnitValue
            if fuArrayFrames[0][index2] in disgust:
                disgustPoints = disgustPoints + faceUnitValue
            if fuArrayFrames[0][index2] in fear:
                fearPoints = fearPoints + faceUnitValue
            if fuArrayFrames[0][index2] in happiness:
                happinessPoints = happinessPoints + faceUnitValue
            if fuArrayFrames[0][index2] in sadness:
                sadnessPoints = sadnessPoints + faceUnitValue
            if fuArrayFrames[0][index2] in surprise:
                surprisePoints = surprisePoints + faceUnitValue

        # divide by the number of fu's in a set, to get average
        # the more fus a set has, the more points it may get
        # if all are found = 1, if no = 0, if half = 0.5 :)
        angerPointsArray.append(angerPoints / 10)
        disgustPointsArray.append(disgustPoints / 6)
        fearPointsArray.append(fearPoints / 8)
        happinessPointsArray.append(happinessPoints / 3)
        sadnessPointsArray.append(sadnessPoints / 6)
        surprisePointsArray.append(surprisePoints / 5)

    finalEmotionPoints = {
        'an': angerPointsArray,
        'ds': disgustPointsArray,
        'fr': fearPointsArray,
        'hp': happinessPointsArray,
        'sd': sadnessPointsArray,
        'sr': surprisePointsArray
    }
    # create dataframe from final emotions points
    finalEmotionPointsDf = pd.DataFrame(finalEmotionPoints)
    return finalEmotionPointsDf


def sumEmotionsAndSaveCsv(finalEmotionPointsDf, session_id):
    # aggregate dataframe by sum of all values
    sumAllEmotions = finalEmotionPointsDf.agg(['sum'])
    # to dict because we cant sort a dataframe after aggregation
    emotionsDict = sumAllEmotions.to_dict('list')

    for emotion, sum in emotionsDict.items():
        emotionsDict[emotion] = sum[0]

    saveResultToCsv(emotionsDict, session_id)
    return 1


def saveResultToCsv(emotionsDict, session_id):
    # save result to a file
    dirPath = default_storage.path(f'tmp/{session_id}')
    if (not os.path.exists(dirPath)):
        os.mkdir(dirPath)

    csvPath = dirPath + "/video_analysis.csv"
    if (exists(csvPath)):
        with open(csvPath, 'a') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow([emotionsDict['an'], emotionsDict['fr'],
                             emotionsDict['hp'], emotionsDict['sd'], emotionsDict['sr']])
    else:
        with open(csvPath, 'a+') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(['an' , 'fr', 'hp', 'sd', 'sr'])
            writer.writerow([emotionsDict['an'], emotionsDict['fr'],
                             emotionsDict['hp'], emotionsDict['sd'], emotionsDict['sr']])
    return 1


def sessionResultsProcessing(session_id):
    finalCsvPath = default_storage.path(f'tmp/{session_id}/video_analysis.csv')
    with open(finalCsvPath, 'r') as file:
        reader = csv.reader(file)
        emotionsArray = []
        emotionsValues = dict()
        for i, row in enumerate(reader):
            if (i == 0):
                for element in row:
                    emotionsArray.append(element)
                    emotionsValues[element] = 0
            else:
                for key, element1 in enumerate(row):
                    if (key < len(emotionsArray)):
                        emotionsValues[emotionsArray[key]] = emotionsValues[emotionsArray[key]] + float(element1)
    valueSum = sum(emotionsValues.values())
    normalizedValues = dict()
    for key, i in emotionsValues.items():
        normalizedValues[key] = round(i * 100 / valueSum, 2)
    # sort descendand to find 2 dominant ones
    sortedEmotions = sorted(normalizedValues.items(), key=lambda x:x[1], reverse=True)
    return normalizedValues
