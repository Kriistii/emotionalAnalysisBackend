from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd
from os.path import exists

import csv
import subprocess

def save_video(video_file, name):
    default_storage.save(
                'tmp/videos/{}.webm'.format(name), ContentFile(video_file.read()))

def analyze_video(identifier):
    video_path = default_storage.path('tmp/videos/{}.mov'.format(identifier))
    openface_path = default_storage.path('OpenFace')
    csv_path = default_storage.path('tmp/csv')
    string = '\\stressWork\\'
    splitResult = openface_path.split(string)
    final_openface_path = splitResult[0] + '\\' + splitResult[1]
    #mac_add = '/build/bin/' add this to path when running it in mac
    print(final_openface_path)
    subprocess.call(f' {final_openface_path}/FeatureExtraction -f {video_path} -aus -out_dir {csv_path} ',
       shell=True)
    mostCommonUnits = csvProcessing2(identifier)
    emotionsPointsDataFrame = findEmotionsPerFrame2(mostCommonUnits)
    dominantEmotions = getTwoDominantEmotions(emotionsPointsDataFrame)
    print(dominantEmotions)

def csvProcessing(identifier):
    with open(default_storage.path('tmp/csv/{}.csv'.format(identifier))) as file:
        fullFinal = []
        headArray = []
        reader = csv.reader(file)
        for i, row in enumerate(reader):
            final = []
            if (i == 0):
                for element1 in row:
                    if ("AU" in element1):
                        # save units to head array (only the unit number)
                        headArray.append(element1[3:5])
                    else:
                        # to preserve the index
                        headArray.append(element1)
            else:
                for index, element in enumerate(row):
                    # get all fu values, only the ones with probability > 0.7
                    if ((float(element) > 0.7) and (index not in [0, 1, 2, 3, 4])):
                        final.append(headArray[index])
                fullFinal.append(final)
    # full final has the best predicted fus
    return fullFinal


def csvProcessing2(identifier):
    with open(default_storage.path('tmp/csv/{}.csv'.format(identifier))) as file:
        fullFinal = []
        headArray = []
        reader = csv.reader(file)
        print(reader)
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
    
    pain = ['04', '06', '07', '09', '10', '12', '20', '25', '26', '27', '43']
    cluelessness = ['01', '02', '05', '15', '17', '22']
    # we also have speech, I ignored it

    finalEmotionPoints = []
    angerPointsArray = []
    disgustPointsArray = []
    fearPointsArray = []
    happinessPointsArray = []
    sadnessPointsArray = []
    surprisePointsArray = []
    painPointsArray = []
    cluelessnessPointsArray = []

    for index, frame in enumerate(fuArrayFrames):
        angerPoints = 0
        disgustPoints = 0
        fearPoints = 0
        happinessPoints = 0
        sadnessPoints = 0
        surprisePoints = 0
        painPoints = 0
        cluelessnessPoints = 0

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
            if fuArrayFrames[0][index2] in pain:
                painPoints = painPoints + faceUnitValue
            if fuArrayFrames[0][index2] in cluelessness:
                cluelessnessPoints = cluelessnessPoints + faceUnitValue

        # divide by the number of fu's in a set, to get average
        # the more fus a set has, the more points it may get
        # if all are found = 1, if no = 0, if half = 0.5 :)
        angerPointsArray.append(angerPoints / 10)
        disgustPointsArray.append(disgustPoints / 6)
        fearPointsArray.append(fearPoints / 8)
        happinessPointsArray.append(happinessPoints / 3)
        sadnessPointsArray.append(sadnessPoints / 6)
        surprisePointsArray.append(surprisePoints / 5)
        painPointsArray.append(painPoints / 11)
        cluelessnessPointsArray.append(cluelessnessPoints / 6)

    finalEmotionPoints = {
        'anger': angerPointsArray,
        'disgust': disgustPointsArray,
        'fear': fearPointsArray,
        'happiness': happinessPointsArray,
        'sadness': sadnessPointsArray,
        'surprise': surprisePointsArray,
        'pain': painPointsArray,
        'cluelessness': cluelessnessPointsArray
    }
    # create dataframe from final emotions points
    finalEmotionPointsDf = pd.DataFrame(finalEmotionPoints)
    return finalEmotionPointsDf


def findEmotionsPerFrame(mostCommonUnits):
    # fu for emotions
    anger = ['04', '05', '07', '10', '17', '22', '23', '24', '25', '26']
    disgust = ['09', '10', '16', '17', '25', '26']
    fear = ['01', '02', '04', '05', '20', '25', '26', '27']
    happiness = ['06', '12', '25']
    sadness = ['01', '04', '06', '11', '15', '17']
    surprise = ['01', '02', '05', '26', '27']

    pain = ['04', '06', '07', '09', '10', '12', '20', '25', '26', '27', '43']
    cluelessness = ['01', '02', '05', '15', '17', '22']
    # we also have speech, I ignored it

    finalEmotionPoints = []
    angerPointsArray = []
    disgustPointsArray = []
    fearPointsArray = []
    happinessPointsArray = []
    sadnessPointsArray = []
    surprisePointsArray = []
    painPointsArray = []
    cluelessnessPointsArray = []

    for frame in mostCommonUnits:
        angerPoints = 0
        disgustPoints = 0
        fearPoints = 0
        happinessPoints = 0
        sadnessPoints = 0
        surprisePoints = 0
        painPoints = 0
        cluelessnessPoints = 0

        # if face unit of frame, is found on emotion set, add 1 to its score
        for faceUnit in frame:
            if faceUnit in anger:
                angerPoints = angerPoints + 1
            if faceUnit in disgust:
                disgustPoints = disgustPoints + 1
            if faceUnit in fear:
                fearPoints = fearPoints + 1
            if faceUnit in happiness:
                happinessPoints = happinessPoints + 1
            if faceUnit in sadness:
                sadnessPoints = sadnessPoints + 1
            if faceUnit in surprise:
                surprisePoints = surprisePoints + 1
            if faceUnit in pain:
                painPoints = painPoints + 1
            if faceUnit in cluelessness:
                cluelessnessPoints = cluelessnessPoints + 1

        # divide by the number of fu's in a set, to get average
        # the more fus a set has, the more points it may get
        # if all are found = 1, if no = 0, if half = 0.5 :)
        angerPointsArray.append(angerPoints / 10)
        disgustPointsArray.append(disgustPoints / 6)
        fearPointsArray.append(fearPoints / 8)
        happinessPointsArray.append(happinessPoints / 3)
        sadnessPointsArray.append(sadnessPoints / 6)
        surprisePointsArray.append(surprisePoints / 5)
        painPointsArray.append(painPoints / 11)
        cluelessnessPointsArray.append(cluelessnessPoints / 6)

    finalEmotionPoints = {
        'anger': angerPointsArray,
        'disgust': disgustPointsArray,
        'fear': fearPointsArray,
        'happiness': happinessPointsArray,
        'sadness': sadnessPointsArray,
        'surprise': surprisePointsArray,
        'pain': painPointsArray,
        'cluelessness': cluelessnessPointsArray
    }
    # create dataframe from final emotions points
    finalEmotionPointsDf = pd.DataFrame(finalEmotionPoints)
    return finalEmotionPointsDf


def getTwoDominantEmotions(finalEmotionPointsDf):
    # aggregate dataframe by sum of all values
    sumAllEmotions = finalEmotionPointsDf.agg(['sum'])
    print(sumAllEmotions)
    # to dict because we cant sort a dataframe after aggregation
    emotionsDict = sumAllEmotions.to_dict('list')
    
    saveResultToCsv(emotionsDict)
    
    for emotion, sum in emotionsDict.items():
        emotionsDict[emotion] = sum[0]
    
    print(emotionsDict)
    # sort descendand to find 2 dominant ones
    sortedEmotions = sorted(emotionsDict.items(), key=lambda x:x[1], reverse=True)

    twoDominant = []
    twoDominant.append(sortedEmotions[0][0])
    twoDominant.append(sortedEmotions[1][0])
    return twoDominant

def saveResultToCsv(emotionsDict):
    #save result to a file
    employeeId = 1 #todo get authenticated user id
    csvPath = default_storage.path('tmp/csv/emotions/{}.csv').format(employeeId)
    if(exists(csvPath)):
        with open(csvPath, 'a') as csvFile:
             writer = csv.writer(csvFile)
             writer.writerow([emotionsDict['anger'], emotionsDict['disgust'], emotionsDict['fear'],
                    emotionsDict['happiness'], emotionsDict['sadness'], emotionsDict['surprise']])
    else:
        #technically a+ will create it if it doesn't exist
        with open(csvPath, 'a+') as csvFile:
             writer = csv.writer(csvFile)
             writer.writerow(['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise'])
             writer.writerow([emotionsDict['anger'], emotionsDict['disgust'], emotionsDict['fear'],
                    emotionsDict['happiness'], emotionsDict['sadness'], emotionsDict['surprise']])
    