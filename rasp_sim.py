from flask import Flask, render_template, request, jsonify, send_file

import requests
import cv2
class InvasionDetector:
    def __init__(self, reference_image):
        if(reference_image is None):
            print("NO REFERENCE!")
            return
        self.reference_frame = reference_image
        self.delta_sides = 110
        self.delta_top = 100
        self.limit = 700
        frame_height, frame_width = self.reference_frame.shape[:2]
        reference_gray = cv2.cvtColor(self.reference_frame, cv2.COLOR_BGR2GRAY)
        reference_blurred = cv2.GaussianBlur(reference_gray, (11, 11), 0)
        reference_edges = cv2.Canny(reference_gray, 80, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 31))
        self.reference_edges = cv2.dilate(reference_edges, kernel, iterations=1)
        self.reference_border_left = reference_edges[self.delta_top:frame_height, 0:self.delta_sides]
        self.reference_border_right = reference_edges[self.delta_top:frame_height, frame_width - self.delta_sides:frame_width]
        self.reference_border_top = reference_edges[0:self.delta_top, 0:frame_width]
        self.reference_cropped = self.reference_frame[self.delta_top:frame_height, self.delta_sides:frame_width - self.delta_sides]
        self.ok_frames = 0
        self.bad_frames = 0
        self.invasion_on = False

    def invasionCheck(self, frame):
        """
        Check if there is an invasion on the input image, compared to the reference.
        Returns  if the cropped image if an invasion is not detected, false otherwise.
        """
        frame_height, frame_width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 150, 200)
        diff = cv2.bitwise_and(edges, cv2.bitwise_not(self.reference_edges))

        border_left = diff[self.delta_top:frame_height, 0:self.delta_sides]
        border_right = diff[self.delta_top:frame_height, frame_width - self.delta_sides:frame_width]
        border_top = diff[0:self.delta_top, 0:frame_width]
        
        cv2.imshow('edges', diff)

        sum = border_left.sum()
        sum += border_right.sum()
        sum += border_top.sum()
        print("Sum: ", sum)
        if sum > self.limit:
            self.ok_frames = 0
            self.bad_frames += 1
            #print('sum:', sum)
            if self.bad_frames and not self.invasion_on:
                #print("Invasion detected!")
                self.invasion_on = True
        else:
            self.ok_frames += 1
            self.bad_frames = 0
            if self.ok_frames > 2 and self.invasion_on:
                self.invasion_on = False
        cropped = frame[self.delta_top:frame_height, self.delta_sides:frame_width - self.delta_sides]
        #if(self.ok_frames > 5 and not self.invasion_on):
            #self.updateReference(edges)
        
        if(not self.invasion_on and self.ok_frames):
            return True, cropped
        else:
            return False, False
    def updateReference(self, new_reference):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 31))
        self.reference_edges = cv2.dilate(new_reference, kernel, iterations=1)


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def mover_boneco(comando):
    return None

def invasion_detection(cap):
    detector = InvasionDetector(frame)

    ret, frame = cap.read()

    invasion_detected = False

    result, cropped = detector.invasionCheck(frame)

    if(not(result)):
        print("Invasion detected!")
        invasion_detected = True

        while (result):
            result, cropped = detector.invasionCheck(frame)
    #     cv2.imshow('frame', cropped)
    #     print("ok")
    # else:

    return invasion_detected

def enviar_requisicao(frame, i):
    filename = './temp_frames/frame_' + str(i).zfill(6) +'.jpg'

    _, encoded_image = cv2.imencode(".jpg", frame)
    image_bytes = encoded_image.tobytes()
    files = {'file': (filename, image_bytes, 'image/jpeg')}

    url = "http://localhost:5000/api/frame_load"
    response = requests.post(url, files=files)

    if response.status_code == 200:
        print("Image sent successfully!")
    else:
        print(f"Error sending image. Status code: {response.status_code}")

@app.route('/frames', methods=['POST'])
def frames():

    cap = cv2.VideoCapture("/dev/video0")
    
    comandos = request.json['comando']
    lgth = len(comandos)
    i = 0

    while i < lgth: 

        comando = comandos[i]

        # invasion = invasion_detection(cap)
        # if invasion:
        #     i -= 5
        #     if i < 0:
        #         i = 0

        #     continue

        mover_boneco(comando)
    
        ret, frame = cap.read()
        enviar_requisicao(frame, i)

        i += 1

if __name__ == '__main__':
    app.run(debug=True, port=5001)
