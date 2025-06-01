from flask import Flask, render_template, request, jsonify, send_file

import requests
import cv2
import numpy as np

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/frames', methods=['POST'])
def frames():
    blocks = request.json

    for block in blocks['comando']:
        i = blocks['comando'].index(block)
        # Create a black image
        image = np.ones((512, 512, 3), np.uint8)* 255

        # Circle parameters
        coordinates = (256 + int(block['X']*10),
                        256 + int(block['Y']*10))
        radius = 25
        color = (50, 50, 255) # White in BGR
        thickness = 2

        # Draw the circle
        cv2.circle(image, coordinates, radius, color, thickness)

        # Display the image
        filename = './temp_frames/frame_' + str(i).zfill(6) +'.jpg'

        _, encoded_image = cv2.imencode(".jpg", image)
        image_bytes = encoded_image.tobytes()
        files = {'file': (filename, image_bytes, 'image/jpeg')}



        url = "http://localhost:5000/api/frame_load"
        response = requests.post(url, files=files)

        if response.status_code == 200:
            print("Image sent successfully!")
        else:
            print(f"Error sending image. Status code: {response.status_code}")


if __name__ == '__main__':
    app.run(debug=True, port=5001)

