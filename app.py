from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for car control
current_speed = 0
current_direction = "STOP"

class VideoCamera:
    def __init__(self):
        # For testing, we'll generate a test pattern
        # Replace this with actual RPi camera when ready
        self.frame_count = 0
        
    def __del__(self):
        pass
    
    def get_frame(self):
        # Generate test video pattern
        self.frame_count += 1
        
        # Create a test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add gradient background
        for i in range(480):
            frame[i, :] = [i//2, (i//3) % 255, 150]
        
        # Add moving circle
        center_x = int(320 + 200 * np.sin(self.frame_count * 0.05))
        center_y = int(240 + 100 * np.cos(self.frame_count * 0.05))
        cv2.circle(frame, (center_x, center_y), 50, (0, 255, 255), -1)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"Test Video Feed", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, timestamp, (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"Frame: {self.frame_count}", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Encode frame
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/control', methods=['POST'])
def control():
    global current_direction, current_speed
    data = request.json
    command = data.get('command', '')
    
    # Process movement commands
    if command in ['forward', 'backward', 'left', 'right', 'stop']:
        current_direction = command.upper()
        print(f"Car Command: {current_direction}")
        # Here you would send commands to RPi GPIO/Motor driver
        
    return jsonify({
        'status': 'success',
        'command': command,
        'direction': current_direction
    })

@socketio.on('joystick_move')
def handle_joystick(data):
    global current_speed, current_direction
    x = data.get('x', 0)
    y = data.get('y', 0)
    
    # Calculate speed and direction from joystick position
    # x: -100 (left) to 100 (right)
    # y: -100 (forward) to 100 (backward)
    
    print(f"Joystick: X={x}, Y={y}")
    
    # Here you would convert joystick values to motor commands
    # and send to RPi
    
    emit('joystick_response', {
        'x': x,
        'y': y,
        'status': 'received'
    })

@app.route('/servo_control', methods=['POST'])
def servo_control():
    data = request.json
    servo_id = data.get('servo_id')
    angle = data.get('angle', 90)
    
    # Ensure angle is within range
    angle = max(0, min(180, angle))
    
    print(f"Servo {servo_id}: {angle}°")
    # Here you would send PWM signal to servo
    # Example with RPi.GPIO:
    # servo_pwm[servo_id].ChangeDutyCycle(angle_to_duty_cycle(angle))
    
    return jsonify({
        'status': 'success',
        'servo_id': servo_id,
        'angle': angle
    })

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

from flask import jsonify, request
from firebase_signalling import FirebaseSignaling
from webrtc_config import *
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase signaling
signaling = FirebaseSignaling('rpi-dashboard-webrtc-firebase-adminsdk-fbsvc-a1d73bace1.json')

def add_webrtc_routes(app):
    """
    Add WebRTC routes to Flask app
    """
    
    @app.route('/webrtc/config')
    def webrtc_config():
        """
        Return WebRTC configuration for client
        """
        return jsonify({
            'iceServers': WEBRTC_CONFIG['iceServers'],
            'roomId': 'rpi_car_stream',
            'deviceId': DASHBOARD_DEVICE_ID
        })
    
    @app.route('/webrtc/offer', methods=['POST'])
    def receive_offer():
        """
        Receive offer from client (not used, client gets from Firebase)
        """
        try:
            data = request.json
            room_id = data.get('roomId')
            offer = data.get('offer')
            
            # Client will get offer from Firebase directly
            return jsonify({'status': 'success'})
        except Exception as e:
            logger.error(f"Error receiving offer: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/webrtc/answer', methods=['POST'])
    def send_answer():
        """
        Send answer to Firebase (backup route, client sends directly)
        """
        try:
            data = request.json
            room_id = data.get('roomId')
            answer = data.get('answer')
            device_id = data.get('deviceId', DASHBOARD_DEVICE_ID)
            
            signaling.send_answer(room_id, answer, device_id)
            
            return jsonify({'status': 'success'})
        except Exception as e:
            logger.error(f"Error sending answer: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/webrtc/ice-candidate', methods=['POST'])
    def add_ice_candidate():
        """
        Add ICE candidate to Firebase (backup route)
        """
        try:
            data = request.json
            room_id = data.get('roomId')
            candidate = data.get('candidate')
            device_id = data.get('deviceId', DASHBOARD_DEVICE_ID)
            
            signaling.add_ice_candidate(room_id, candidate, device_id)
            
            return jsonify({'status': 'success'})
        except Exception as e:
            logger.error(f"Error adding ICE candidate: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/webrtc/status/<room_id>')
    def get_room_status(room_id):
        """
        Get current room status
        """
        try:
            status = signaling.get_room_status(room_id)
            return jsonify({
                'status': status,
                'roomId': room_id
            })
        except Exception as e:
            logger.error(f"Error getting room status: {e}")
            return jsonify({'error': str(e)}), 500

# WebRTC Configuration Route
@app.route('/webrtc/config')
def webrtc_config():
    """Return WebRTC and Firebase configuration for client"""
    import os
    
    firebase_web_config = {
        'apiKey': os.getenv('FIREBASE_API_KEY', 'AIzaSyDGxQ7_your_api_key_here'),
        'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN', 'your-project.firebaseapp.com'),
        'projectId': os.getenv('FIREBASE_PROJECT_ID', 'your-project-id'),
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'your-project.appspot.com'),
        'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID', '123456789'),
        'appId': os.getenv('FIREBASE_APP_ID', '1:123456789:web:abc123')
    }
    
    return jsonify({
        'firebase': firebase_web_config,
        'roomId': 'rpi_car_stream',
        'deviceId': 'dashboard_viewer',
        'iceServers': [
            {'urls': 'stun:stun.l.google.com:19302'},
            {'urls': 'stun:stun1.l.google.com:19302'},
            {'urls': 'stun:stun2.l.google.com:19302'}
        ]
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

