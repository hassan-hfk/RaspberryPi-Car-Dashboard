"""
WebRTC Configuration for Raspberry Pi Car Dashboard
"""

# WebRTC Configuration
WEBRTC_CONFIG = {
    'iceServers': [
        # Google STUN servers
        {'urls': 'stun:stun.l.google.com:19302'},
        {'urls': 'stun:stun1.l.google.com:19302'},
        {'urls': 'stun:stun2.l.google.com:19302'},
        {'urls': 'stun:stun3.l.google.com:19302'},
        {'urls': 'stun:stun4.l.google.com:19302'},
    ]
}

# Firebase Configuration
# You'll get these values from Firebase Console
FIREBASE_CONFIG = {
    'type': 'service_account',
    'project_id': 'your-project-id',
    'private_key_id': 'your-private-key-id',
    'private_key': 'your-private-key',
    'client_email': 'your-client-email',
    'client_id': 'your-client-id',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': 'your-cert-url'
}

# Firestore collection names
FIREBASE_SIGNALING_COLLECTION = 'webrtc_signaling'
FIREBASE_OFFERS_COLLECTION = 'offers'
FIREBASE_ANSWERS_COLLECTION = 'answers'
FIREBASE_ICE_CANDIDATES_COLLECTION = 'ice_candidates'

# Device IDs
RPI_DEVICE_ID = 'rpi_car_camera'  # Raspberry Pi (sender)
DASHBOARD_DEVICE_ID = 'dashboard_viewer'  # Dashboard (receiver)

# Video Settings
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
VIDEO_FPS = 30
VIDEO_BITRATE = 1000000  # 1 Mbps

# Connection Settings
CONNECTION_TIMEOUT = 30  # seconds
RECONNECT_DELAY = 5  # seconds
MAX_RECONNECT_ATTEMPTS = 3