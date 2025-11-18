"""
Firebase Signaling Server for WebRTC
Handles SDP exchange and ICE candidate exchange
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
import logging
from datetime import datetime
from webrtc_config import *

logger = logging.getLogger(__name__)

class FirebaseSignaling:
    def __init__(self, config_path=None):
        """
        Initialize Firebase connection
        config_path: Path to Firebase service account JSON file
        """
        try:
            if config_path:
                cred = credentials.Certificate(config_path)
            else:
                # Use config from webrtc_config.py
                cred = credentials.Certificate(FIREBASE_CONFIG)
            
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            self.signaling_ref = self.db.collection(FIREBASE_SIGNALING_COLLECTION)
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Firebase initialization failed: {e}")
            raise
    
    def create_room(self, room_id):
        """Create a new signaling room"""
        try:
            room_ref = self.signaling_ref.document(room_id)
            room_ref.set({
                'created_at': firestore.SERVER_TIMESTAMP,
                'status': 'waiting',
                'offer': None,
                'answer': None
            })
            logger.info(f"Room created: {room_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create room: {e}")
            return False
    
    def send_offer(self, room_id, offer_sdp, device_id):
        """Send WebRTC offer (from RPi camera)"""
        try:
            room_ref = self.signaling_ref.document(room_id)
            room_ref.update({
                'offer': {
                    'sdp': offer_sdp,
                    'type': 'offer',
                    'from': device_id,
                    'timestamp': firestore.SERVER_TIMESTAMP
                },
                'status': 'offer_sent'
            })
            logger.info(f"Offer sent to room: {room_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send offer: {e}")
            return False
    
    def send_answer(self, room_id, answer_sdp, device_id):
        """Send WebRTC answer (from dashboard)"""
        try:
            room_ref = self.signaling_ref.document(room_id)
            room_ref.update({
                'answer': {
                    'sdp': answer_sdp,
                    'type': 'answer',
                    'from': device_id,
                    'timestamp': firestore.SERVER_TIMESTAMP
                },
                'status': 'answer_sent'
            })
            logger.info(f"Answer sent to room: {room_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send answer: {e}")
            return False
    
    def add_ice_candidate(self, room_id, candidate, device_id):
        """Add ICE candidate"""
        try:
            ice_ref = self.signaling_ref.document(room_id).collection('ice_candidates')
            ice_ref.add({
                'candidate': candidate,
                'from': device_id,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"ICE candidate added to room: {room_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add ICE candidate: {e}")
            return False
    
    def get_offer(self, room_id):
        """Get offer from room"""
        try:
            room_ref = self.signaling_ref.document(room_id)
            doc = room_ref.get()
            if doc.exists:
                data = doc.to_dict()
                return data.get('offer')
            return None
        except Exception as e:
            logger.error(f"Failed to get offer: {e}")
            return None
    
    def get_answer(self, room_id):
        """Get answer from room"""
        try:
            room_ref = self.signaling_ref.document(room_id)
            doc = room_ref.get()
            if doc.exists:
                data = doc.to_dict()
                return data.get('answer')
            return None
        except Exception as e:
            logger.error(f"Failed to get answer: {e}")
            return None
    
    def get_ice_candidates(self, room_id, device_id):
        """Get ICE candidates for specific device"""
        try:
            ice_ref = self.signaling_ref.document(room_id).collection('ice_candidates')
            candidates = []
            
            # Get candidates not from this device
            docs = ice_ref.where('from', '!=', device_id).stream()
            
            for doc in docs:
                data = doc.to_dict()
                candidates.append(data['candidate'])
            
            return candidates
        except Exception as e:
            logger.error(f"Failed to get ICE candidates: {e}")
            return []
    
    def listen_for_offer(self, room_id, callback):
        """Listen for offer changes (for dashboard)"""
        try:
            room_ref = self.signaling_ref.document(room_id)
            
            def on_snapshot(doc_snapshot, changes, read_time):
                for doc in doc_snapshot:
                    data = doc.to_dict()
                    if data.get('offer'):
                        callback(data['offer'])
            
            # Watch for changes
            room_ref.on_snapshot(on_snapshot)
            logger.info(f"Listening for offer on room: {room_id}")
        except Exception as e:
            logger.error(f"Failed to listen for offer: {e}")
    
    def listen_for_answer(self, room_id, callback):
        """Listen for answer changes (for RPi)"""
        try:
            room_ref = self.signaling_ref.document(room_id)
            
            def on_snapshot(doc_snapshot, changes, read_time):
                for doc in doc_snapshot:
                    data = doc.to_dict()
                    if data.get('answer'):
                        callback(data['answer'])
            
            # Watch for changes
            room_ref.on_snapshot(on_snapshot)
            logger.info(f"Listening for answer on room: {room_id}")
        except Exception as e:
            logger.error(f"Failed to listen for answer: {e}")
    
    def listen_for_ice_candidates(self, room_id, device_id, callback):
        """Listen for new ICE candidates"""
        try:
            ice_ref = self.signaling_ref.document(room_id).collection('ice_candidates')
            
            def on_snapshot(col_snapshot, changes, read_time):
                for change in changes:
                    if change.type.name == 'ADDED':
                        data = change.document.to_dict()
                        if data.get('from') != device_id:
                            callback(data['candidate'])
            
            # Watch for new candidates
            ice_ref.on_snapshot(on_snapshot)
            logger.info(f"Listening for ICE candidates on room: {room_id}")
        except Exception as e:
            logger.error(f"Failed to listen for ICE candidates: {e}")
    
    def cleanup_room(self, room_id):
        """Delete room and all its data"""
        try:
            # Delete ICE candidates
            ice_ref = self.signaling_ref.document(room_id).collection('ice_candidates')
            docs = ice_ref.stream()
            for doc in docs:
                doc.reference.delete()
            
            # Delete room
            self.signaling_ref.document(room_id).delete()
            logger.info(f"Room cleaned up: {room_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup room: {e}")
            return False
    
    def get_room_status(self, room_id):
        """Get current room status"""
        try:
            room_ref = self.signaling_ref.document(room_id)
            doc = room_ref.get()
            if doc.exists:
                data = doc.to_dict()
                return data.get('status', 'unknown')
            return None
        except Exception as e:
            logger.error(f"Failed to get room status: {e}")
            return None