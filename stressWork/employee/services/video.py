from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd
from os.path import exists

import csv
import subprocess
import cv2
import os
import shutil

def save_video(video_file, name):
    default_storage.save(
                'tmp/videos/{}.webm'.format(name), ContentFile(video_file.read()))

def analyze_video(identifier):
    #get paths, for video processing
    video_path = default_storage.path('tmp/videos/{}.mov'.format(identifier))
    openface_path = default_storage.path('OpenFace')
    csv_path = default_storage.path('tmp/csv')
    string = '\\stressWork\\'
    splitResult = openface_path.split(string)
    final_openface_path = splitResult[0] + '\\' + splitResult[1]
    #mac_add = '/build/bin/' add this to path when running it in mac

    #get video duration
    video = cv2.VideoCapture(video_path)
    frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = video.get(cv2.CAP_PROP_FPS) 
    duration = frame_count / fps


    start = 0
    #create dir to store all 1s videos
    os.mkdir(default_storage.path('tmp/videos/{}'.format(identifier)))
    while(duration > 1):
        end = start + 1
        #create duration slots
        if(start < 10):
            startString = "0" + str(start)
        else :
            startString = str(start)
        
        if(end < 10):
            endString = "0" + str(end)
        else :
            endString = str(end)

        duration = duration - 1
        outputPath = default_storage.path('tmp/videos/{}/{}.mov'.format(identifier,end))
        #split video in 1s videos
        subprocess.run(f" ffmpeg -i {video_path} -ss  00:00:{startString} -to  00:00:{endString} -c copy {outputPath}", shell=True)
        #run video analysis for each video
        subprocess.call(f' {final_openface_path}/FeatureExtraction -f {outputPath} -aus -out_dir {csv_path} ',
        shell=True)

        #emotion analysis
        mostCommonUnits = csvProcessing2(end)
        emotionsPointsDataFrame = findEmotionsPerFrame2(mostCommonUnits)
        dominantEmotions = getTwoDominantEmotions(emotionsPointsDataFrame)
        start = end

    #shutil.rmtree(default_storage.path('tmp/videos/{}'.format(identifier)))
    return 1
    

def csvProcessing2(identifier):
    with open(default_storage.path('tmp/csv/{}.csv'.format(identifier))) as file:
        fullFinal = []
        headArray = []
        reader = csv.reader(file)
        for i, row in enumerate(reader):
            final = []
            if (i == 0):
                for element1 in row:
                    if ("_r" in element1):
                        # save units to head array (only the unit number)
                        headArray.append(element1[3:5])
                fullFinal.append(headArray)
            else:
                for index, element in enumerate(row):
                    # get all fu values, only the ones with probability > 0.7
                    if 5 <= index <= 21:
                        final.append(float(element))
                fullFinal.append(final)
    # full final has the best predicted fus
    return fullFinal

def findEmotionsPerFrame2(fuArrayFrames):
    # fu for emotions
    anger = ['04', '05', '07', '10', '17', '22', '23', '24', '25', '26']
    disgust = ['09', '10', '16', '17', '25', '26']
    fear = ['01', '02', '04', '05', '20', '25', '26', '27']
    happiness = ['06', '12', '25']
    sadness = ['01', '04', '06', '11', '15', '17']
    surprise = ['01', '02', '05', '26', '27']

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
        'anger': angerPointsArray,
        'disgust': disgustPointsArray,
        'fear': fearPointsArray,
        'happiness': happinessPointsArray,
        'sadness': sadnessPointsArray,
        'surprise': surprisePointsArray
    }
    # create dataframe from final emotions points
    finalEmotionPointsDf = pd.DataFrame(finalEmotionPoints)
    return finalEmotionPointsDf

def getTwoDominantEmotions(finalEmotionPointsDf):
    # aggregate dataframe by sum of all values
    sumAllEmotions = finalEmotionPointsDf.agg(['sum'])
    # to dict because we cant sort a dataframe after aggregation
    emotionsDict = sumAllEmotions.to_dict('list')


    for emotion, sum in emotionsDict.items():
        emotionsDict[emotion] = sum[0]
        
    saveResultToCsv(emotionsDict)
    
    # sort descendand to find 2 dominant ones
    sortedEmotions = sorted(emotionsDict.items(), key=lambda x:x[1], reverse=True)

    twoDominant = []
    twoDominant.append(sortedEmotions[0][0])
    twoDominant.append(sortedEmotions[1][0])
    return twoDominant

def saveResultToCsv(emotionsDict):
    #save result to a file
    employeeId = 1 #todo get authenticated user id, or set uniqueid idk
    dirPath = default_storage.path('tmp/csv/emotionAnalysis')
    if(not os.path.exists(dirPath)):
        os.mkdir(dirPath)

    csvPath = dirPath + f"/{employeeId}.csv"
    if(exists(csvPath)):
        with open(csvPath, 'a') as csvFile:
             writer = csv.writer(csvFile)
             writer.writerow([emotionsDict['anger'], emotionsDict['disgust'], emotionsDict['fear'],
                    emotionsDict['happiness'], emotionsDict['sadness'], emotionsDict['surprise']])
    else:
        with open(csvPath, 'a+') as csvFile:
             writer = csv.writer(csvFile)
             writer.writerow(['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise'])
             writer.writerow([emotionsDict['anger'], emotionsDict['disgust'], emotionsDict['fear'],
                    emotionsDict['happiness'], emotionsDict['sadness'], emotionsDict['surprise']])
    return 1
    