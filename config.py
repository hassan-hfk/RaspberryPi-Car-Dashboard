"""
Configuration file for Raspberry Pi Car Dashboard
Modify these settings according to your hardware setup
"""

# Flask Configuration
FLASK_HOST = '0.0.0.0'  # Allow external connections
FLASK_PORT = 5000
FLASK_DEBUG = True
SECRET_KEY = 'change-this-to-a-random-secret-key'

# Video Configuration
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
VIDEO_FPS = 30
USE_TEST_VIDEO = True  # Set to False when using actual RPi camera

# GPIO Pin Configuration (BCM Mode)
# L298N Motor Driver Pins
MOTOR_LEFT_FORWARD = 17
MOTOR_LEFT_BACKWARD = 27
MOTOR_LEFT_ENABLE = 18  # PWM pin for speed control

MOTOR_RIGHT_FORWARD = 22
MOTOR_RIGHT_BACKWARD = 23
MOTOR_RIGHT_ENABLE = 24  # PWM pin for speed control

# Motor Speed Settings (0-100)
DEFAULT_SPEED = 70
MAX_SPEED = 100
MIN_SPEED = 30

# GSM Module Configuration
GSM_SERIAL_PORT = '/dev/ttyUSB0'
GSM_BAUD_RATE = 9600
GSM_TIMEOUT = 1

# Camera Configuration
CAMERA_TYPE = 'picamera'  # Options: 'picamera', 'usb', 'test'
CAMERA_ROTATION = 0  # 0, 90, 180, or 270 degrees
CAMERA_HFLIP = False  # Horizontal flip
CAMERA_VFLIP = False  # Vertical flip

# Network Configuration
ENABLE_EXTERNAL_ACCESS = True
SOCKETIO_PING_TIMEOUT = 60
SOCKETIO_PING_INTERVAL = 25

# Safety Features
AUTO_STOP_TIMEOUT = 5  # Seconds of inactivity before auto-stop
ENABLE_AUTO_STOP = True
MAX_COMMAND_RATE = 50  # Maximum commands per second

# Joystick Configuration
JOYSTICK_DEADZONE = 20  # Threshold for joystick movement (0-100)
JOYSTICK_SENSITIVITY = 1.0  # Multiplier for joystick input

# System Monitoring
ENABLE_BATTERY_MONITOR = False  # Set to True if battery monitoring is available
BATTERY_PIN = 4  # GPIO pin for battery voltage reading
BATTERY_WARNING_LEVEL = 20  # Percentage

# Logging Configuration
ENABLE_LOGGING = True
LOG_FILE = 'car_dashboard.log'
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL