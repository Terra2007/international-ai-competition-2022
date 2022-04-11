from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import serial
import cv2

from threading import Thread
import time

scale_status = 1
scale_flag = 0

def create_app(app, socket_io:SocketIO, arduino:serial.Serial):
    @app.route('/')
    def index():
        """Video streaming home page."""
        return render_template('index.html', scale=scale_status**2)

    def run_model(frame):
        print("running model!")
        for i in range(5000): print(i)
        print("model run end!")
        result_location = 0
        arduino.write(f'{result_location}'.encode('utf-8'))
        # arduino serial control
        return


    def gen():
        cap = cv2.VideoCapture(1)
        prev_time = time.time()
        while True:
            suc, frame = cap.read()
            if suc:
                frame = cv2.imencode('.jpg', frame)[1].tobytes()
                yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                time.sleep(0.033)
                end_time = time.time()
                if end_time - prev_time > 10:
                    thread = Thread(target=run_model, args=(frame,))
                    thread.daemon = True
                    prev_time = time.time()
                    thread.start()
            else:
                break

    @app.route('/video_feed')
    def video_feed():
        return Response(gen(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    @socket_io.on("startmove")
    def start_move(message):
        message = str(message)
        arduino.write(message.encode('utf-8'))

    @socket_io.on("endmove")
    def end_move():
        arduino.write('0'.encode('utf-8'))

    @socket_io.on("startcloseup")
    def start_closeup(message):
        global scale_status, scale_flag

        scale_flag = 1

        print("Start CloseUP")

        while scale_flag == 1:
            scale_status += 0.01 * message

            if scale_status > 1: scale_status = 1
            elif scale_status < 0: scale_status = 0

            socket_io.emit('scroll', {"scale_status" : scale_status})
            time.sleep(0.1)

    @socket_io.on("endcloseup")
    def end_closeup():
        global scale_flag
        scale_flag = 0
        print("End CloseUP")

if __name__ == '__main__':
    app = Flask(__name__)
    app.secret_key = "FlaskSecret"
    socket_io = SocketIO(app, cors_allowed_origins="*")

    arduino = serial.Serial('COM9', 9600)

    create_app(app, socket_io, arduino)
    socket_io.run(app, host='0.0.0.0', port=5000)