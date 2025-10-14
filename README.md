# Raspberry Pi Car Control Dashboard

A Flask-based web dashboard for controlling a Raspberry Pi car with live video streaming, directional controls, and joystick interface.

## Features

- 🎥 **Live Video Streaming** - Real-time camera feed from Raspberry Pi
- 🕹️ **Dual Control Methods**
  - Directional buttons (Forward, Backward, Left, Right, Stop)
  - Interactive joystick control
- 🔄 **Real-time Communication** - WebSocket-based control using Socket.IO
- 📊 **System Monitoring** - Display GSM signal, battery, camera, and motor status
- ⌨️ **Keyboard Controls** - W/A/S/D or Arrow keys for control
- 📱 **Responsive Design** - Works on desktop and mobile devices

## Project Structure

```
rpi-car-dashboard/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── static/
│   ├── css/
│   │   └── style.css              # Dashboard styling
│   └── js/
│       └── script.js              # Frontend JavaScript logic
└── templates/
    └── index.html                 # Main dashboard HTML
```

## Installation

### 1. Clone or Create the Project

Create the directory structure as shown above and copy all files into their respective locations.

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python app.py
```

The dashboard will be available at: `http://localhost:5000`

## Usage

### Button Controls
- Click and hold directional buttons to move the car
- Release button to automatically stop
- Click **STOP** button for emergency stop

### Joystick Control
- Click and drag the joystick in any direction
- Release to stop
- Real-time X/Y coordinates displayed below joystick

### Keyboard Controls
- **W** or **↑** - Forward
- **S** or **↓** - Backward
- **A** or **←** - Left
- **D** or **→** - Right
- **Space** - Stop

## Raspberry Pi Integration

### Hardware Requirements
- Raspberry Pi (3/4/Zero W)
- Pi Camera Module or USB Camera
- GSM Module (SIM800/SIM900)
- L298N Motor Driver
- DC Motors
- Power Supply

### Connecting to Raspberry Pi Camera

Replace the `VideoCamera` class in `app.py` with:

```python
import cv2

class VideoCamera:
    def __init__(self):
        # For Raspberry Pi Camera Module
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
    def __del__(self):
        if self.camera:
            self.camera.release()
    
    def get_frame(self):
        success, frame = self.camera.read()
        if not success:
            return None
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()
```

### Motor Control Integration

Add GPIO control in `app.py`:

```python
import RPi.GPIO as GPIO

# GPIO Pin Configuration
MOTOR_LEFT_FWD = 17
MOTOR_LEFT_BWD = 27
MOTOR_RIGHT_FWD = 22
MOTOR_RIGHT_BWD = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR_LEFT_FWD, GPIO.OUT)
GPIO.setup(MOTOR_LEFT_BWD, GPIO.OUT)
GPIO.setup(MOTOR_RIGHT_FWD, GPIO.OUT)
GPIO.setup(MOTOR_RIGHT_BWD, GPIO.OUT)

def motor_forward():
    GPIO.output(MOTOR_LEFT_FWD, GPIO.HIGH)
    GPIO.output(MOTOR_LEFT_BWD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_FWD, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_BWD, GPIO.LOW)

def motor_backward():
    GPIO.output(MOTOR_LEFT_FWD, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_BWD, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_FWD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_BWD, GPIO.HIGH)

def motor_left():
    GPIO.output(MOTOR_LEFT_FWD, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_BWD, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_FWD, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_BWD, GPIO.LOW)

def motor_right():
    GPIO.output(MOTOR_LEFT_FWD, GPIO.HIGH)
    GPIO.output(MOTOR_LEFT_BWD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_FWD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_BWD, GPIO.HIGH)

def motor_stop():
    GPIO.output(MOTOR_LEFT_FWD, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_BWD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_FWD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_BWD, GPIO.LOW)

# Update the control route
@app.route('/control', methods=['POST'])
def control():
    data = request.json
    command = data.get('command', '')
    
    if command == 'forward':
        motor_forward()
    elif command == 'backward':
        motor_backward()
    elif command == 'left':
        motor_left()
    elif command == 'right':
        motor_right()
    elif command == 'stop':
        motor_stop()
    
    return jsonify({'status': 'success', 'command': command})
```

## Network Configuration

### Local Network Access
Access from other devices on the same network:
```
http://<raspberry-pi-ip>:5000
```

### Port Forwarding
To access over the internet, configure port forwarding on your router:
- Forward external port 5000 to Raspberry Pi's port 5000
- Access via: `http://<your-public-ip>:5000`

### Using GSM Module
Configure the GSM module to enable remote access via mobile network.

## Security Considerations

For production deployment:

1. **Change the secret key** in `app.py`
2. **Add authentication** - Implement user login
3. **Use HTTPS** - Set up SSL certificates
4. **Firewall rules** - Restrict access to specific IPs
5. **Rate limiting** - Prevent abuse

## Troubleshooting

### Video Stream Not Loading
- Check camera connection
- Verify OpenCV installation: `python -c "import cv2; print(cv2.__version__)"`
- Test camera separately: `raspistill -o test.jpg`

### Controls Not Responding
- Check browser console for errors (F12)
- Verify Socket.IO connection status
- Check Flask server logs

### High Latency
- Reduce video resolution in camera settings
- Use wired Ethernet instead of WiFi
- Optimize video encoding settings

## License

MIT License - Feel free to modify and use for your projects!

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

- Flask framework
- Socket.IO for real-time communication
- OpenCV for video processing