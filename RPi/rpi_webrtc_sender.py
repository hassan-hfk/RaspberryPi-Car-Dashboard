"""
Raspberry Pi WebRTC Video Sender
Captures video from camera and streams via WebRTC
"""

import asyncio
import cv2
import logging
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer
from av import VideoFrame
import numpy as np
from firebase_signaling import FirebaseSignaling
from webrtc_config import *
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraVideoTrack(VideoStreamTrack):
    """
    Video track that reads from Raspberry Pi camera
    """
    def __init__(self, camera_id=0):
        super().__init__()
        self.camera = cv2.VideoCapture(camera_id)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_HEIGHT)
        self.camera.set(cv2.CAP_PROP_FPS, VIDEO_FPS)
        
        if not self.camera.isOpened():
            raise Exception("Could not open camera")
        
        logger.info(f"Camera initialized: {VIDEO_WIDTH}x{VIDEO_HEIGHT}@{VIDEO_FPS}fps")
    
    async def recv(self):
        """
        Read frame from camera and return as VideoFrame
        """
        pts, time_base = await self.next_timestamp()
        
        # Read frame from camera
        ret, frame = self.camera.read()
        
        if not ret:
            logger.error("Failed to read frame from camera")
            return None
        
        # Convert BGR to RGB (OpenCV uses BGR, WebRTC uses RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create VideoFrame
        video_frame = VideoFrame.from_ndarray(frame_rgb, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        
        return video_frame
    
    def __del__(self):
        if hasattr(self, 'camera'):
            self.camera.release()


class RPiWebRTCSender:
    def __init__(self, room_id, firebase_config_path=None):
        self.room_id = room_id
        self.device_id = RPI_DEVICE_ID
        self.pc = None
        self.signaling = FirebaseSignaling(firebase_config_path)
        self.video_track = None
        self.connected = False
        
    async def start(self):
        """
        Start WebRTC connection and send video
        """
        try:
            # Create peer connection
            self.pc = RTCPeerConnection(configuration=WEBRTC_CONFIG)
            
            # Create video track from camera
            self.video_track = CameraVideoTrack()
            self.pc.addTrack(self.video_track)
            
            logger.info("Video track added to peer connection")
            
            # Set up event handlers
            @self.pc.on("connectionstatechange")
            async def on_connectionstatechange():
                logger.info(f"Connection state: {self.pc.connectionState}")
                if self.pc.connectionState == "connected":
                    self.connected = True
                    logger.info("✅ WebRTC connection established!")
                elif self.pc.connectionState == "failed":
                    self.connected = False
                    logger.error("❌ WebRTC connection failed")
                    await self.reconnect()
            
            @self.pc.on("icecandidate")
            async def on_icecandidate(candidate):
                if candidate:
                    logger.info(f"New ICE candidate: {candidate}")
                    self.signaling.add_ice_candidate(
                        self.room_id,
                        {
                            'candidate': candidate.candidate,
                            'sdpMLineIndex': candidate.sdpMLineIndex,
                            'sdpMid': candidate.sdpMid
                        },
                        self.device_id
                    )
            
            # Create room
            self.signaling.create_room(self.room_id)
            
            # Create and send offer
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)
            
            self.signaling.send_offer(
                self.room_id,
                {
                    'type': self.pc.localDescription.type,
                    'sdp': self.pc.localDescription.sdp
                },
                self.device_id
            )
            
            logger.info("Offer sent, waiting for answer...")
            
            # Listen for answer
            answer_received = asyncio.Event()
            
            def on_answer(answer_data):
                asyncio.create_task(self.handle_answer(answer_data, answer_received))
            
            self.signaling.listen_for_answer(self.room_id, on_answer)
            
            # Listen for ICE candidates
            def on_ice_candidate(candidate_data):
                asyncio.create_task(self.handle_ice_candidate(candidate_data))
            
            self.signaling.listen_for_ice_candidates(
                self.room_id,
                self.device_id,
                on_ice_candidate
            )
            
            # Wait for connection
            logger.info("Waiting for dashboard to connect...")
            await answer_received.wait()
            
            # Keep running
            while self.connected:
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in sender: {e}")
            raise
    
    async def handle_answer(self, answer_data, event):
        """
        Handle received answer from dashboard
        """
        try:
            answer = RTCSessionDescription(
                sdp=answer_data['sdp'],
                type=answer_data['type']
            )
            await self.pc.setRemoteDescription(answer)
            logger.info("Answer received and set as remote description")
            event.set()
        except Exception as e:
            logger.error(f"Failed to handle answer: {e}")
    
    async def handle_ice_candidate(self, candidate_data):
        """
        Handle received ICE candidate
        """
        try:
            from aiortc import RTCIceCandidate
            
            candidate = RTCIceCandidate(
                candidate=candidate_data['candidate'],
                sdpMLineIndex=candidate_data['sdpMLineIndex'],
                sdpMid=candidate_data['sdpMid']
            )
            await self.pc.addIceCandidate(candidate)
            logger.info("ICE candidate added")
        except Exception as e:
            logger.error(f"Failed to add ICE candidate: {e}")
    
    async def reconnect(self):
        """
        Attempt to reconnect
        """
        logger.info("Attempting to reconnect...")
        await asyncio.sleep(RECONNECT_DELAY)
        await self.stop()
        await self.start()
    
    async def stop(self):
        """
        Stop WebRTC connection and cleanup
        """
        try:
            if self.pc:
                await self.pc.close()
            
            if self.video_track:
                self.video_track.stop()
            
            self.signaling.cleanup_room(self.room_id)
            logger.info("Sender stopped and cleaned up")
        except Exception as e:
            logger.error(f"Error stopping sender: {e}")


async def main():
    """
    Main entry point for Raspberry Pi sender
    """
    room_id = "rpi_car_stream"
    
    # Path to your Firebase service account JSON
    firebase_config = "firebase_service_account.json"
    
    sender = RPiWebRTCSender(room_id, firebase_config)
    
    try:
        logger.info(f"Starting RPi WebRTC sender for room: {room_id}")
        await sender.start()
    except KeyboardInterrupt:
        logger.info("Stopping sender...")
    finally:
        await sender.stop()


if __name__ == "__main__":
    asyncio.run(main())