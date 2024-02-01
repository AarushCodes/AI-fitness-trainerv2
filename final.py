import cv2
import numpy as np
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

from sklearn.preprocessing import LabelEncoder
from tensorflow import keras
from tensorflow.keras import layers
import speech_recognition as sr
import queue
import threading
import registrationandemail
import os
import pyttsx3
import re

def normalize_landmarks(landmarks):
    x_values = []
    y_values = []
    for landmark in landmarks:

        x_values.append(landmark.x)
        y_values.append(landmark.y)

    min_x = min(x_values)
    min_y = min(y_values)
    normalized_x  = [x - min_x for x in x_values]

    normalized_y = [y- min_y for y in y_values]

    normalized_landmarks = [item for pair in zip(normalized_x, normalized_y) for item in pair]

    return normalized_landmarks

def isnarroworwide(feetlandmarks):

    legonedifference = feetlandmarks[1] - feetlandmarks[3]
    legtwodifference = feetlandmarks[2] - feetlandmarks[0]

    if (legonedifference > -0.01 and legonedifference < 0.01) or (legtwodifference > -0.01 and legtwodifference < 0.01) :
        status = 'perfect'
    elif legonedifference > 0.01 or legtwodifference > 0.01:
        status = 'wide'
    elif legonedifference < -0.01 or legtwodifference < -0.01:
        status = 'narrow'

    else:
        status = 'NA'
    return status

def are_legs_too_open_or_closed(landmarks):
    diff1 = landmarks[30] - landmarks[12]
    diff2 = landmarks[11] -  landmarks[29]
    if (diff1 > -0.015 and diff1 < 0.015) or (diff2 > -0.015 and diff2 < 0.015):
        status = 'perfect'
    elif diff1< -0.015 or diff2< -0.015:
        status = 'too open'
    elif diff1 > 0.015 or diff2< 0.015:
        status = 'too closed'
    else:
        status = 'NA'

    return status

class checkExcercise:

    def __init__(self, state):
        self.state = state
        self.totalcurls = 0

    def calculateangle(self,a,b,c): 
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians*180/np.pi)

        if angle > 180:
            angle = 360 - angle
        return angle

    def isbackstraight(self,landmarks):
        rshoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        relbow = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        rwrist = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        angle = self.calculateangle(rshoulder,relbow,rwrist)

        if angle >175:
            return True
    def isBicepCurl(self,landmarks,mode='Left'):

        if mode == 'Left':

            lshoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            lelbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            lwrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            angle = self.calculateangle(lshoulder,lelbow,lwrist)
            if angle > 160:

                    self.state = 'down'
            if angle < 30 and self.state =='down':

                    self.state = 'up'

                    return True

        elif mode == 'Right':

            rshoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            relbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            rwrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            angle = self.calculateangle(rshoulder,relbow,rwrist)
            if angle > 160:

                self.state = 'down'
            if angle < 30 and self.state =='down':

                self.state = 'up'
                return True
        elif mode == 'Both':

            rshoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            relbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            rwrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            lshoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            lelbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            lwrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            rangle = self.calculateangle(rshoulder,relbow,rwrist)
            langle = self.calculateangle(lshoulder,lelbow,lwrist)
            if rangle > 160 and langle > 160:

                self.state = 'down'
            if rangle < 30 and langle < 30 and self.state =='down':

                self.state = 'up'
                return True

def recognize_speech(recognizer,result_queue,microphone):
    while True:
        with microphone as source:
            print("Say something:")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
        try:
            recognized_text = recognizer.recognize_google(audio,language='en-in')

            result_queue.put(recognized_text)
        except sr.UnknownValueError:

            pass
        except sr.RequestError as e:

            pass

'''recognizer = sr.Recognizer()
microphone = sr.Microphone()
recognize_speech(recognizer,microphone)
'''

def parse_workout_schedule(text):

    lines = text.split('\n')

    workout_schedule = {
        'Monday': None,
        'Tuesday': None,
        'Wednesday': None,
        'Thursday': None,
        'Friday': None,
        'Saturday': None,
        'Sunday': None
    }

    for line in lines:
        if line.strip().startswith('Workouts:'):
            workouts_line = line
            break

    workouts = workouts_line.strip().split(': ')[1].split(', ')

    for line in lines:
        if line.strip().startswith('Workout Days:'):
            workout_days_line = line.strip()
            break

    workout_days = workout_days_line.split(': ')[1].split(', ')

    for day, workout in zip(workout_days, workouts):
        workout_schedule[day.strip()] = workout.strip()

    return workout_schedule

def bicepworkout(image,imgbackground,reps,total_reps):
    data = {}
    try:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        results = pose.process(image)
        landmarks = results.pose_landmarks.landmark

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        isbicepcurl = checkExcercise.isBicepCurl(landmarks,mode='Both')
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                    mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
                                    mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2) 
                                    ) 

        backstraight = checkExcercise.isbackstraight(landmarks)
        if backstraight:
            imgbackground[0:720, 798:1280] = perfectmode
        else:
            imgbackground[0:720, 798:1280] = wrongmode
            cv2.putText(imgbackground, 'Your back is not straight', (738+100,500), font, font_scale, font_color, font_thickness, cv2.LINE_AA)
        cv2.putText(imgbackground, str(reps), (738+250,200), font, 3, font_color, 5, cv2.LINE_AA)

        if isbicepcurl and backstraight:
            reps += 1
            total_reps +=1
        elif isbicepcurl:
            total_reps +=1
        imgbackground[171:171+480, 69:69+640] = image
        data = {
        'reps': reps,
        'total reps': total_reps
        }
    except Exception as e:
        print(e)                

    data['imgbackground'] = imgbackground
    return data

def squatworkout(image,imgbackground,squatreps,total_reps):
    global state,bgstate
    data = {}
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image.flags.writeable = False

    results = pose.process(image)

    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    try:
        landmarks = results.pose_landmarks.landmark

        normalized_landmarks = normalize_landmarks(landmarks)
        testdata = np.array([normalized_landmarks])
        predictions = model.predict(testdata)
        predicted_classes = (predictions > 0.5).astype(int)

        upordown = label_encoder.inverse_transform(predicted_classes.flatten()).tolist()[0]
        landmarks = [landmark.x for landmark in landmarks]

        narroworwide = isnarroworwide(landmarks[-4:])
        too_open_or_closed = are_legs_too_open_or_closed(landmarks)
        if narroworwide == 'perfect' and too_open_or_closed == 'perfect':
            imgbackground[0:720, 798:1280] = perfectmode
            if upordown == 'down':
                state = 'down'
            if upordown == 'up' and state =='down':
                state = 'up'
                squatreps += 1

        else:
            imgbackground[0:720, 798:1280] = wrongmode
            if upordown == 'down':
                bgstate = 'down'
            if upordown == 'up' and bgstate =='down':
                bgstate = 'up'
                total_reps += 1
            y_position = 500

            wronglines = []
            if narroworwide == 'wide':
                wronglines.append('Your toes are facing outwards')
            elif narroworwide == 'narrow':
                wronglines.append('Your toes are facing inwards')

            if too_open_or_closed == 'too open':
                wronglines.append('Your legs are too open')
            elif too_open_or_closed == 'too closed':
                wronglines.append('Your legs are too closed')

            for line in wronglines:
                cv2.putText(imgbackground, line, (738+80, y_position), font, font_scale, font_color, font_thickness, cv2.LINE_AA)
                y_position += 60
        cv2.putText(imgbackground, str(squatreps), (738+250,200), font, 3, font_color, 5, cv2.LINE_AA)

        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
                                mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2) 
                                ) 
        data = {
        'reps': squatreps,
        'total reps': total_reps,

        }

    except Exception as e:
        print(e)

    imgbackground[171:171+480, 69:69+640] = image
    data['imgbackground'] = imgbackground
    cv2.imshow('Your gym buddy', imgbackground)
    return data

email_sender = registrationandemail.SendEmail(sender_email='aarush.chirag@gmail.com',apppassword='YOUR_GOOGLE_APPPASSWORD')
os.environ['PATH'] += ":/opt/homebrew/bin"
sr.AudioFile.SRC_FLAC = "/opt/homebrew/bin/flac"
engine = pyttsx3.init()

recognizer = sr.Recognizer()
model = keras.models.load_model('model2.h5')
label_encoder = LabelEncoder()
label_encoder = label_encoder.fit(['up', 'down'])
selection = -1
counter = 0
selection_speed = 7
squatorbicepcentres = [(1038, 273), (1038, 559)]
selectbicepcentres = [(798+150,214), (798+330, 395), (798+150,576)]
backgroundimg = cv2.imread('backgroundimage.png')
bgimg = cv2.imread('backgroundimage copy.png')

perfectmode = cv2.imread('perfect.png')
wrongmode = cv2.imread('wrongv2.png')

bicepmode = cv2.imread('bicep.png')
checkExcercise = checkExcercise(state='None')
state = 'unknown'
bgstate = 'unknown'
stage = 'bicep'
bicepsaid = False
squatsaid = False
reps = 0
total_reps = 0
total_bicep_reps = 0
squatreps = 0
bicepreps= 0
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1
font_thickness = 2
font_color = (255, 255, 255)
checkhands = True
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) 
mode = ''
cap = cv2.VideoCapture(0)

microphone = sr.Microphone()
result_queue = queue.Queue()

if os.path.isfile("user_data.txt"):
    with open("user_data.txt") as file:
         user_data = file.read()
         email = re.search(r'Email:\s*([\w.-]+@[\w.-]+)', user_data)
         email = email.group(1)
    workout_schedule = parse_workout_schedule(user_data)
    recognition_thread = threading.Thread(target=recognize_speech, args=(recognizer, result_queue,microphone))

    recognition_thread.start()
    today_workout = registrationandemail.get_today_workout(workout_schedule)
    tomorrow_workout = registrationandemail.get_tomorrow_workout(workout_schedule)
    yesterday_workout = registrationandemail.get_yesterday_workout(workout_schedule)
    bicepset = 2
    squatset = 2
    while True: 
        ret, image = cap.read()
        imgbackground = backgroundimg
        image = cv2.resize(image,(640,480))

        imgbackground[171:171+480, 69:69+640] = image
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if not result_queue.empty():
            recognized_text = result_queue.get()
            print(recognized_text)

            if 'exit program' in recognized_text:
                break
            elif 'exit current mode' in recognized_text:
                mode = ''
                reps = total_reps = squatreps = bicepreps = 0
                imgbackground = backgroundimg.copy()
            elif "what is today's workout" in recognized_text:
                if today_workout:
                    engine.say(f"Today's workout is a {today_workout.strip()} Workout")
                    engine.runAndWait() 
                else:
                    engine.say("There is no workout today")
                    engine.runAndWait()
            elif "what was yesterday's workout" in recognized_text:
                 if yesterday_workout:
                    engine.say(f"Yesterday's workout was a {yesterday_workout.strip()} Workout")
                    engine.runAndWait() 
                 else:
                      engine.say("There was no workout yesterday")
                      engine.runAndWait()
            elif "what is tomorrow's workout" in recognized_text:
                 if tomorrow_workout:
                      engine.say(f"Tomorrow's workout is a {tomorrow_workout.strip()} workout")
                      engine.runAndWait()
                 else:
                      engine.say("There is no workout tomorrow")
                      engine.runAndWait()
            elif "start today's workout" in recognized_text:
                 if today_workout:
                      if today_workout.strip() == 'Full Body':
                           mode = 'Full Body'
                      elif today_workout.strip() == 'Lower Body':
                         mode= 'Lower Body'
                      else:
                           mode = 'Upper Body'
            elif "start upper body workout" in recognized_text.lower():
                 mode = 'Upper Body'
            elif "start lower body workout" in recognized_text.lower():
                 mode = 'Lower Body'
            elif "start full body workout" in recognized_text.lower():
                 mode = 'Full Body'

            elif 'squat mod' in recognized_text:
                mode = 'squats'
            elif 'bicep mod' in recognized_text:
                if 'left' in recognized_text:
                    mode = 'Left bicep'
                elif 'right' in recognized_text:
                    mode = 'Right bicep'
                else:
                    mode = 'Both bicep'
        if mode == "Lower Body":
             if squatsaid == False:
                engine.say(f'We are going to start the Lower Body workout. We are going to do {squatset} squats!')
                engine.runAndWait()
                bicepsaid = squatsaid = True
             if squatreps < squatset:
                data = squatworkout(image=image,imgbackground=imgbackground,squatreps=squatreps,total_reps=total_reps)

                if 'reps' in data:
                    squatreps = data['reps']
                    total_reps = data['total reps']
                imgbackground = data['imgbackground']
                cv2.imshow('Your gym buddy', imgbackground)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

             else:
                  bicepsaid = squatsaid = False
                  incorrect_reps = total_reps - reps
                  print('workout completed')
                  message = (f'''Workout Summary:
Workout: Lower Body
Correctly done squats: {reps}
Incorrectly done squatsL {incorrect_reps}''')
                  imgbackground[0:720, 798:1280] = bgimg[0:720, 798:1280]

                  cv2.putText(imgbackground, 'Workout Completed!', (738+100,100), font, 1.25, font_color, font_thickness, cv2.LINE_AA)
                  cv2.putText(imgbackground, f"Correct reps: {reps}", (738+100,100+100), font, 1.25, font_color, font_thickness, cv2.LINE_AA)
                  cv2.putText(imgbackground,  f"Incorrect reps: {incorrect_reps}", (738+100,100+200), font, 1.25, font_color, font_thickness, cv2.LINE_AA)
                  engine.say("Bravo! You've successfully finished your workout! Keep pushing towards your goals!")
                  engine.runAndWait()
                  email_sender.Send_Email(email,'Workout Summary',message,mode='text')
                  incorrect_reps = 0
                  mode = ''
                  squatreps = 0
                  total_reps = 0

        elif mode =='Upper Body':
            if bicepsaid == False:
                 engine.say(f'We are going to start Upper Body workout. We are going to do {bicepset} bicep curls!')
                 engine.runAndWait()
                 bicepsaid = squatsaid = True
            if reps < bicepset:
                data = bicepworkout(image=image,imgbackground=imgbackground,reps=reps,total_reps=total_reps)
                if 'reps' in data:
                     reps = data['reps']
                     total_reps = data['total reps']

                imgbackground = data['imgbackground']

                cv2.imshow('Your gym buddy', imgbackground)
            else:
                 incorrect_reps = total_reps - reps
                 bicepsaid = squatsaid = False

                 imgbackground[0:720, 798:1280] = bgimg[0:720, 798:1280]

                 cv2.putText(imgbackground, 'Workout Completed!', (738+100,100), font, 1.25, font_color, font_thickness, cv2.LINE_AA)
                 cv2.putText(imgbackground, f"Correct reps: {reps}", (738+100,100+100), font, 1.25, font_color, font_thickness, cv2.LINE_AA)
                 cv2.putText(imgbackground,  f"Incorrect reps: {incorrect_reps}", (738+100,100+200), font, 1.25, font_color, font_thickness, cv2.LINE_AA)
                 engine.say("Bravo! You've successfully finished your workout! Keep pushing towards your goals!")
                 engine.runAndWait()
                 message = (f'Workout Summary:\nWorkout: Upper Body\nCorrectly done bicep curls: {reps}\nIncorrectly done bicep curls {incorrect_reps}')
                 email_sender.Send_Email(email.strip(),'Workout Summary',message,mode='text')
                 mode = ''
                 reps = 0
                 total_reps = 0
                 bicepreps =0
                 squatreps = 0
                 print('workout completed')
            if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

        elif mode == 'Full Body':
            if stage =='bicep' and bicepsaid == False:
                engine.say(f'We are going to start the Full Body workout. First we are going to do {bicepset} bicep curls!')
                engine.runAndWait()
                bicepsaid  = True
            elif squatsaid == False and bicepreps>=bicepset: 
                engine.say(f'Now, we are going to do {squatset} squats!')
                engine.runAndWait()
                squatsaid=True
            if bicepreps < bicepset:
                 data = bicepworkout(image=image,imgbackground=imgbackground,reps=bicepreps,total_reps=total_bicep_reps)
                 if 'reps' in data:
                      bicepreps = data['reps']
                      total_bicep_reps = data['total reps']
                 imgbackground = data['imgbackground']
                 cv2.imshow('Your gym buddy', imgbackground)

            elif bicepreps >= bicepset and squatreps < squatset:
                 stage = 'squats'
                 total_reps=0
                 data = squatworkout(image=image,imgbackground=imgbackground,squatreps=squatreps,total_reps=total_reps)

                 if 'reps' in data:

                      squatreps = data['reps']
                      total_squat_reps = data['total reps']

                 imgbackground = data['imgbackground']
                 cv2.imshow('Your gym buddy', imgbackground)

            else:
                 bicepsaid = squatsaid = False
                 incorrect_bicepcurls = total_bicep_reps - bicepreps
                 incorrect_squats = total_squat_reps - squatreps
                 imgbackground[0:720, 798:1280] = bgimg[0:720, 798:1280]
                 cv2.putText(imgbackground, 'Workout Completed!', (738+100,100), font, 1.25, font_color, font_thickness, cv2.LINE_AA)
                 cv2.putText(imgbackground, f"Correct bicep reps: {bicepreps}", (738+100,100+100), font, 1.25, font_color, font_thickness, cv2.LINE_AA)
                 cv2.putText(imgbackground,  f"Incorrect bicep reps: {incorrect_bicepcurls}", (738+100,100+170), font, 1.25, font_color, font_thickness, cv2.LINE_AA)
                 cv2.putText(imgbackground,  f"Correct squat reps: {incorrect_squats}", (738+100,100+240), font, 1.25, font_color, font_thickness, cv2.LINE_AA)
                 cv2.putText(imgbackground,  f"Incorrect squat reps: {incorrect_squats}", (738+100,100+310), font, 1.25, font_color, font_thickness, cv2.LINE_AA)
                 engine.say("Bravo! You've successfully finished your workout! Keep pushing towards your goals!")
                 engine.runAndWait()
                 message = (f'''Workout Summary:
Workout: Full Body
Correctly done bicep curls: {bicepreps}
Incorrectly done bicep curls {incorrect_bicepcurls}
Correctly done squats: {squatreps}
Incorrectly done squats: {incorrect_squats}''')
                 email_sender.Send_Email(email,'Workout Summary',message,mode='text')
                 mode = ''
                 total_reps = 0
                 bicepreps = 0
                 squatreps = 0
                 reps =0             
            if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        elif mode == 'squats':

                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                image.flags.writeable = False

                results = pose.process(image)

                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                try:
                    landmarks = results.pose_landmarks.landmark

                    normalized_landmarks = normalize_landmarks(landmarks)
                    testdata = np.array([normalized_landmarks])
                    predictions = model.predict(testdata)
                    predicted_classes = (predictions > 0.5).astype(int)

                    upordown = label_encoder.inverse_transform(predicted_classes.flatten()).tolist()[0]
                    landmarks = [landmark.x for landmark in landmarks]

                    narroworwide = isnarroworwide(landmarks[-4:])
                    too_open_or_closed = are_legs_too_open_or_closed(landmarks)

                    if narroworwide == 'perfect' and too_open_or_closed == 'perfect':
                        imgbackground[0:720, 798:1280] = perfectmode
                        if upordown == 'down':
                            state = 'down'
                        if upordown == 'up' and state =='down':
                            state = 'up'
                            reps += 1
                    else:
                        imgbackground[0:720, 798:1280] = wrongmode
                        y_position = 500

                        wronglines = []
                        if narroworwide == 'wide':
                            wronglines.append('Your toes are facing outwards')
                        elif narroworwide == 'narrow':
                            wronglines.append('Your toes are facing inwards')

                        if too_open_or_closed == 'too open':
                            wronglines.append('Your legs are too open')
                        elif too_open_or_closed == 'too closed':
                            wronglines.append('Your legs are too closed')

                        for line in wronglines:
                            cv2.putText(imgbackground, line, (738+80, y_position), font, font_scale, font_color, font_thickness, cv2.LINE_AA)
                            y_position += 60
                    cv2.putText(imgbackground, str(reps), (738+250,200), font, 3, font_color, 5, cv2.LINE_AA)

                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                            mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
                                            mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2) 
                                            ) 
                except Exception as e:
                    print(e)

                imgbackground[171:171+480, 69:69+640] = image
                cv2.imshow('Your gym buddy', imgbackground)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

        elif 'bicep' in mode:

            try:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False

                results = pose.process(image)
                landmarks = results.pose_landmarks.landmark

                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                isbicepcurl = checkExcercise.isBicepCurl(landmarks,mode=mode.removesuffix(' bicep'))
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                            mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
                                            mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2) 
                                            ) 
                backstraight = checkExcercise.isbackstraight(landmarks)
                if backstraight:
                    imgbackground[0:720, 798:1280] = perfectmode
                else:
                    imgbackground[0:720, 798:1280] = wrongmode
                    cv2.putText(imgbackground, 'Your back is not straight', (738+100,500), font, font_scale, font_color, font_thickness, cv2.LINE_AA)

                if isbicepcurl and backstraight:
                    reps += 1
                    total_reps +=1
                elif isbicepcurl:
                    total_reps +=1
                imgbackground[171:171+480, 69:69+640] = image

            except:
                pass

            cv2.putText(imgbackground, str(reps), (738+250,200), font, 3, font_color, 5, cv2.LINE_AA)
            cv2.imshow('Your gym buddy', imgbackground)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                        break 

        if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        else:

          cv2.imshow('Your gym buddy', imgbackground)
else:
     engine.say("As this is the first time you are using this program, you will have to register and then restart the program.")
     engine.runAndWait()
     registrationandemail.start()
cap.release()
cv2.destroyAllWindows()