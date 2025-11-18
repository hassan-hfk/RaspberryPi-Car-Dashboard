/**
 * WebRTC Client for Dashboard
 * Receives video stream from Raspberry Pi
 */

// Import Firebase (add this to HTML head)
// <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
// <script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore-compat.js"></script>

class WebRTCClient {
    constructor(firebaseConfig, roomId, deviceId) {
        this.firebaseConfig = firebaseConfig;
        this.roomId = roomId;
        this.deviceId = deviceId;
        this.pc = null;
        this.db = null;
        this.remoteStream = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        
        this.initFirebase();
    }
    
    initFirebase() {
        try {
            // Initialize Firebase
            if (!firebase.apps.length) {
                firebase.initializeApp(this.firebaseConfig);
            }
            this.db = firebase.firestore();
            console.log('✅ Firebase initialized');
        } catch (error) {
            console.error('❌ Firebase initialization failed:', error);
        }
    }
    
    async start(videoElement) {
        try {
            console.log(`🚀 Starting WebRTC client for room: ${this.roomId}`);
            
            // Create peer connection
            this.pc = new RTCPeerConnection({
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' },
                    { urls: 'stun:stun2.l.google.com:19302' }
                ]
            });
            
            // Handle incoming tracks
            this.pc.ontrack = (event) => {
                console.log('📹 Received remote track');
                if (event.streams && event.streams[0]) {
                    videoElement.srcObject = event.streams[0];
                    this.remoteStream = event.streams[0];
                    this.updateConnectionStatus('streaming');
                }
            };
            
            // Handle connection state changes
            this.pc.onconnectionstatechange = () => {
                console.log(`🔄 Connection state: ${this.pc.connectionState}`);
                this.updateConnectionStatus(this.pc.connectionState);
                
                if (this.pc.connectionState === 'connected') {
                    this.connected = true;
                    this.reconnectAttempts = 0;
                    console.log('✅ WebRTC connected!');
                } else if (this.pc.connectionState === 'failed') {
                    this.connected = false;
                    console.error('❌ WebRTC connection failed');
                    this.handleConnectionFailure();
                } else if (this.pc.connectionState === 'disconnected') {
                    this.connected = false;
                    console.warn('⚠️ WebRTC disconnected');
                }
            };
            
            // Handle ICE candidates
            this.pc.onicecandidate = (event) => {
                if (event.candidate) {
                    console.log('🧊 New ICE candidate');
                    this.sendIceCandidate(event.candidate);
                }
            };
            
            // Handle ICE connection state
            this.pc.oniceconnectionstatechange = () => {
                console.log(`🧊 ICE connection state: ${this.pc.iceConnectionState}`);
            };
            
            // Listen for offers from RPi
            this.listenForOffers();
            
            // Listen for ICE candidates
            this.listenForIceCandidates();
            
            console.log('👂 Listening for WebRTC offer from RPi...');
            
        } catch (error) {
            console.error('❌ Error starting WebRTC client:', error);
            throw error;
        }
    }
    
    listenForOffers() {
        const roomRef = this.db.collection('webrtc_signaling').doc(this.roomId);
        
        roomRef.onSnapshot(async (snapshot) => {
            if (snapshot.exists) {
                const data = snapshot.data();
                
                if (data.offer && !this.pc.currentRemoteDescription) {
                    console.log('📨 Received offer from RPi');
                    await this.handleOffer(data.offer);
                }
            }
        }, (error) => {
            console.error('❌ Error listening for offers:', error);
        });
    }
    
    async handleOffer(offerData) {
        try {
            console.log('🔧 Processing offer...');
            
            const offer = new RTCSessionDescription({
                type: offerData.type,
                sdp: offerData.sdp
            });
            
            await this.pc.setRemoteDescription(offer);
            console.log('✅ Remote description set');
            
            // Create answer
            const answer = await this.pc.createAnswer();
            await this.pc.setLocalDescription(answer);
            console.log('✅ Local description set');
            
            // Send answer to Firebase
            await this.sendAnswer(answer);
            console.log('✅ Answer sent to RPi');
            
        } catch (error) {
            console.error('❌ Error handling offer:', error);
        }
    }
    
    async sendAnswer(answer) {
        try {
            const roomRef = this.db.collection('webrtc_signaling').doc(this.roomId);
            
            await roomRef.update({
                answer: {
                    sdp: answer.sdp,
                    type: answer.type,
                    from: this.deviceId,
                    timestamp: firebase.firestore.FieldValue.serverTimestamp()
                },
                status: 'answer_sent'
            });
            
            console.log('📤 Answer uploaded to Firebase');
        } catch (error) {
            console.error('❌ Error sending answer:', error);
        }
    }
    
    async sendIceCandidate(candidate) {
        try {
            const iceRef = this.db.collection('webrtc_signaling')
                .doc(this.roomId)
                .collection('ice_candidates');
            
            await iceRef.add({
                candidate: candidate.candidate,
                sdpMLineIndex: candidate.sdpMLineIndex,
                sdpMid: candidate.sdpMid,
                from: this.deviceId,
                timestamp: firebase.firestore.FieldValue.serverTimestamp()
            });
            
            console.log('📤 ICE candidate sent');
        } catch (error) {
            console.error('❌ Error sending ICE candidate:', error);
        }
    }
    
    listenForIceCandidates() {
        const iceRef = this.db.collection('webrtc_signaling')
            .doc(this.roomId)
            .collection('ice_candidates');
        
        iceRef.where('from', '!=', this.deviceId)
            .onSnapshot((snapshot) => {
                snapshot.docChanges().forEach(async (change) => {
                    if (change.type === 'added') {
                        const data = change.doc.data();
                        console.log('🧊 Received ICE candidate from RPi');
                        
                        try {
                            const candidate = new RTCIceCandidate({
                                candidate: data.candidate,
                                sdpMLineIndex: data.sdpMLineIndex,
                                sdpMid: data.sdpMid
                            });
                            
                            await this.pc.addIceCandidate(candidate);
                            console.log('✅ ICE candidate added');
                        } catch (error) {
                            console.error('❌ Error adding ICE candidate:', error);
                        }
                    }
                });
            }, (error) => {
                console.error('❌ Error listening for ICE candidates:', error);
            });
    }
    
    updateConnectionStatus(status) {
        // Update UI with connection status
        const statusElement = document.getElementById('webrtc-status');
        if (statusElement) {
            const statusMap = {
                'new': '🔵 Initializing...',
                'connecting': '🟡 Connecting...',
                'connected': '🟢 Connected',
                'streaming': '📹 Streaming',
                'disconnected': '🔴 Disconnected',
                'failed': '❌ Connection Failed',
                'closed': '⚫ Closed'
            };
            
            statusElement.textContent = statusMap[status] || status;
            statusElement.className = `webrtc-status status-${status}`;
        }
    }
    
    handleConnectionFailure() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            
            setTimeout(() => {
                this.reconnect();
            }, 5000);
        } else {
            console.error('❌ Max reconnection attempts reached');
            this.updateConnectionStatus('failed');
        }
    }
    
    async reconnect() {
        console.log('🔄 Reconnecting...');
        await this.stop();
        
        const videoElement = document.getElementById('video-stream');
        if (videoElement) {
            await this.start(videoElement);
        }
    }
    
    async stop() {
        try {
            if (this.pc) {
                this.pc.close();
                this.pc = null;
            }
            
            if (this.remoteStream) {
                this.remoteStream.getTracks().forEach(track => track.stop());
                this.remoteStream = null;
            }
            
            this.connected = false;
            console.log('🛑 WebRTC client stopped');
        } catch (error) {
            console.error('❌ Error stopping client:', error);
        }
    }
    
    getStats() {
        if (this.pc) {
            return this.pc.getStats();
        }
        return null;
    }
}

// Initialize WebRTC when page loads
let webrtcClient = null;

async function initWebRTC() {
    try {
        console.log('🎬 Initializing WebRTC...');
        
        // Firebase configuration
        const firebaseConfig = {
            apiKey: "YOUR_API_KEY",
            authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
            projectId: "YOUR_PROJECT_ID",
            storageBucket: "YOUR_PROJECT_ID.appspot.com",
            messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
            appId: "YOUR_APP_ID"
        };
        
        const roomId = 'rpi_car_stream';
        const deviceId = 'dashboard_viewer';
        
        webrtcClient = new WebRTCClient(firebaseConfig, roomId, deviceId);
        
        const videoElement = document.getElementById('video-stream');
        if (videoElement) {
            // Change img to video element
            videoElement.autoplay = true;
            videoElement.playsInline = true;
            
            await webrtcClient.start(videoElement);
            console.log('✅ WebRTC initialized successfully');
        }
        
    } catch (error) {
        console.error('❌ WebRTC initialization failed:', error);
    }
}

// Auto-start WebRTC on page load
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for Firebase to load
    setTimeout(() => {
        initWebRTC();
    }, 1000);
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (webrtcClient) {
        webrtcClient.stop();
    }
});