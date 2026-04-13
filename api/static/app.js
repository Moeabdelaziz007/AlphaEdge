/**
 * AlphaEdge Holographic Neural Link
 * Three.js WebGL + WebSocket + Web Speech API + Telegram Mini App
 * Zero text input. Voice-first. Spatial visualization.
 */

// ═══════════════════════════════════════════
//  TELEGRAM MINI APP INTEGRATION
// ═══════════════════════════════════════════

const isTMA = Boolean(window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData);
let tgWebApp = null;

if (isTMA) {
    tgWebApp = window.Telegram.WebApp;
    tgWebApp.expand();                   // Full-screen mode inside Telegram
    tgWebApp.enableClosingConfirmation(); // Prevent accidental close
    
    // Sync background to Telegram's dark theme
    const bgColor = tgWebApp.themeParams?.bg_color || '#010101';
    document.body.style.backgroundColor = bgColor;
    
    // Signal ready when Three.js canvas is loaded (deferred below)
    console.log('[TMA] Running inside Telegram Mini App');
} else {
    console.log('[TMA] Running in standalone browser mode');
}

// ═══════════════════════════════════════════
//  THREE.JS SCENE SETUP
// ═══════════════════════════════════════════

const canvas = document.getElementById('hologram-canvas');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
camera.position.z = 5;

// HUD Elements
const stateLabel = document.getElementById('state-label');
const resultCard = document.getElementById('result-card');
const resultContent = document.getElementById('result-content');
const voiceIndicator = document.getElementById('voice-indicator');
const waveformCanvas = document.getElementById('waveform-canvas');
const waveformCtx = waveformCanvas.getContext('2d');
const skillFeed = document.getElementById('skill-feed');
const skillLabel = document.getElementById('skill-label');

// ═══════════════════════════════════════════
//  NEURAL PARTICLE SYSTEM
// ═══════════════════════════════════════════

const PARTICLE_COUNT = 500;
const positions = new Float32Array(PARTICLE_COUNT * 3);
const velocities = [];
const baseColors = new Float32Array(PARTICLE_COUNT * 3);

for (let i = 0; i < PARTICLE_COUNT; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 8;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 8;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 8;
    velocities.push({
        x: (Math.random() - 0.5) * 0.005,
        y: (Math.random() - 0.5) * 0.005,
        z: (Math.random() - 0.5) * 0.005
    });
    // Default cyan
    baseColors[i * 3] = 0;
    baseColors[i * 3 + 1] = 0.9;
    baseColors[i * 3 + 2] = 1;
}

const particleGeo = new THREE.BufferGeometry();
particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
particleGeo.setAttribute('color', new THREE.BufferAttribute(baseColors, 3));

const particleMat = new THREE.PointsMaterial({
    size: 0.04,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending,
    depthWrite: false
});

const particles = new THREE.Points(particleGeo, particleMat);
scene.add(particles);

// Neural connection lines
const lineMat = new THREE.LineBasicMaterial({
    color: 0x00e5ff,
    transparent: true,
    opacity: 0.08,
    blending: THREE.AdditiveBlending
});

const lineGeo = new THREE.BufferGeometry();
const linePositions = new Float32Array(200 * 6); // 200 connection lines
lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
const lines = new THREE.LineSegments(lineGeo, lineMat);
scene.add(lines);

// Central glowing orb
const orbGeo = new THREE.SphereGeometry(0.4, 32, 32);
const orbMat = new THREE.MeshBasicMaterial({
    color: 0x00e5ff,
    transparent: true,
    opacity: 0.3
});
const orb = new THREE.Mesh(orbGeo, orbMat);
scene.add(orb);

// ═══════════════════════════════════════════
//  STATE MACHINE COLOR MAP
// ═══════════════════════════════════════════

const STATE_COLORS = {
    idle:              { r: 0, g: 0.9, b: 1,   orbColor: 0x00e5ff, lineOpacity: 0.08, speed: 1 },
    listening:         { r: 0, g: 1,   b: 0.53, orbColor: 0x00ff88, lineOpacity: 0.15, speed: 2 },
    reflecting:        { r: 0.18, g: 0.36, b: 1, orbColor: 0x2f5dff, lineOpacity: 0.2, speed: 3 },
    skill_building:    { r: 1, g: 0.2, b: 0.4,  orbColor: 0xff3366, lineOpacity: 0.35, speed: 5 },
    jules_dispatching: { r: 0.6, g: 0, b: 1,    orbColor: 0x9900ff, lineOpacity: 0.4, speed: 4 },
    code_matrix:       { r: 0, g: 1, b: 0.3,    orbColor: 0x00ff4c, lineOpacity: 0.5, speed: 6 },
    executing:         { r: 1, g: 0.6, b: 0,    orbColor: 0xff9900, lineOpacity: 0.25, speed: 4 },
    speaking:          { r: 1, g: 0.84, b: 0,   orbColor: 0xffd700, lineOpacity: 0.3, speed: 2 },
    result:            { r: 0, g: 0.9, b: 1,    orbColor: 0x00e5ff, lineOpacity: 0.08, speed: 1 }
};

let currentState = STATE_COLORS.idle;
let particleSpeed = 1;

function setVisualState(stateName) {
    const s = STATE_COLORS[stateName] || STATE_COLORS.idle;
    currentState = s;
    particleSpeed = s.speed;

    // Animate orb color
    orb.material.color.setHex(s.orbColor);
    lineMat.opacity = s.lineOpacity;

    // Shift particle colors
    const colors = particleGeo.attributes.color.array;
    for (let i = 0; i < PARTICLE_COUNT; i++) {
        colors[i * 3] = s.r + (Math.random() * 0.1);
        colors[i * 3 + 1] = s.g + (Math.random() * 0.1);
        colors[i * 3 + 2] = s.b + (Math.random() * 0.1);
    }
    particleGeo.attributes.color.needsUpdate = true;
}

// ═══════════════════════════════════════════
//  ANIMATION LOOP
// ═══════════════════════════════════════════

let time = 0;

function animate() {
    requestAnimationFrame(animate);
    time += 0.01 * particleSpeed;

    const pos = particleGeo.attributes.position.array;

    // Animate particles with subtle drift
    for (let i = 0; i < PARTICLE_COUNT; i++) {
        pos[i * 3] += velocities[i].x * particleSpeed;
        pos[i * 3 + 1] += velocities[i].y * particleSpeed;
        pos[i * 3 + 2] += velocities[i].z * particleSpeed;

        // Boundary wrap
        if (Math.abs(pos[i * 3]) > 4) velocities[i].x *= -1;
        if (Math.abs(pos[i * 3 + 1]) > 4) velocities[i].y *= -1;
        if (Math.abs(pos[i * 3 + 2]) > 4) velocities[i].z *= -1;
    }
    particleGeo.attributes.position.needsUpdate = true;

    // Update neural connection lines (connect nearby particles)
    const lp = lineGeo.attributes.position.array;
    let lineIdx = 0;
    for (let i = 0; i < 80 && lineIdx < 200 * 6; i++) {
        const a = Math.floor(Math.random() * PARTICLE_COUNT);
        const b = Math.floor(Math.random() * PARTICLE_COUNT);
        const dx = pos[a*3] - pos[b*3], dy = pos[a*3+1] - pos[b*3+1], dz = pos[a*3+2] - pos[b*3+2];
        if (dx*dx + dy*dy + dz*dz < 3) {
            lp[lineIdx++] = pos[a*3]; lp[lineIdx++] = pos[a*3+1]; lp[lineIdx++] = pos[a*3+2];
            lp[lineIdx++] = pos[b*3]; lp[lineIdx++] = pos[b*3+1]; lp[lineIdx++] = pos[b*3+2];
        }
    }
    lineGeo.attributes.position.needsUpdate = true;

    // Orb breathing
    const scale = 1 + Math.sin(time * 2) * 0.15;
    orb.scale.set(scale, scale, scale);
    orb.material.opacity = 0.2 + Math.sin(time * 3) * 0.1;

    // Slow camera orbit
    camera.position.x = Math.sin(time * 0.1) * 0.5;
    camera.position.y = Math.cos(time * 0.15) * 0.3;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
}
animate();

// Signal Telegram Mini App that the hologram is fully loaded
if (isTMA && tgWebApp) tgWebApp.ready();
// Resize handler
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// ═══════════════════════════════════════════
//  WEBSOCKET CONNECTION
// ═══════════════════════════════════════════

const wsProtocol = location.protocol === 'https:' ? 'wss' : 'ws';
const ws = new WebSocket(`${wsProtocol}://${location.host}/ws`);

ws.onopen = () => {
    stateLabel.textContent = 'NEURAL LINK ACTIVE';
    setVisualState('idle');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const state = data.state || 'idle';

    // Update visual state
    setVisualState(state);

    // Update HUD label
    if (data.label) {
        stateLabel.textContent = data.label.toUpperCase();
    }

    // Show/hide skill building feed
    if (state === 'skill_building') {
        skillFeed.classList.remove('hidden');
        skillLabel.textContent = data.label || 'FORGING...';
    } else {
        skillFeed.classList.add('hidden');
    }

    // Handle result display
    if (data.result) {
        resultContent.textContent = data.result;
        resultCard.classList.remove('hidden');
        stateLabel.textContent = 'TAP HOLOGRAM TO CONTINUE';

        // Speak the result
        speakResult(data.result);

        // Auto-hide after 20s
        setTimeout(() => resultCard.classList.add('hidden'), 20000);
    }

    if (state === 'idle' && !data.result) {
        stateLabel.textContent = 'READY FOR LINK';
        resultCard.classList.add('hidden');
    }
};

ws.onerror = () => stateLabel.textContent = 'CONNECTION ERROR';
ws.onclose = () => {
    stateLabel.textContent = 'NEURAL LINK SEVERED';
    setVisualState('idle');
};

// ═══════════════════════════════════════════
//  WEB SPEECH API (Voice Input / TTS Output)
// ═══════════════════════════════════════════

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isListening = false;

// Audio Analyzer for waveform visualization
let audioCtx, analyser, micSource, dataArray;

async function setupAudioAnalyzer(stream) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    micSource = audioCtx.createMediaStreamSource(stream);
    micSource.connect(analyser);
    dataArray = new Uint8Array(analyser.frequencyBinCount);
    drawWaveform();
}

function drawWaveform() {
    if (!isListening) return;
    requestAnimationFrame(drawWaveform);
    analyser.getByteFrequencyData(dataArray);

    waveformCtx.clearRect(0, 0, 300, 60);
    const barWidth = 300 / dataArray.length * 2;
    let x = 0;
    for (let i = 0; i < dataArray.length; i++) {
        const barHeight = (dataArray[i] / 255) * 60;
        waveformCtx.fillStyle = `rgba(0, 255, 136, ${dataArray[i]/255})`;
        waveformCtx.fillRect(x, 60 - barHeight, barWidth - 1, barHeight);
        x += barWidth;
    }

    // Feed audio amplitude to the orb size for real-time reactivity
    const avg = dataArray.reduce((a,b) => a+b, 0) / dataArray.length;
    const orbScale = 1 + (avg / 255) * 0.8;
    orb.scale.set(orbScale, orbScale, orbScale);
}

function startListening() {
    if (!SpeechRecognition) {
        stateLabel.textContent = 'NO STT SUPPORT IN BROWSER';
        return;
    }
    if (isListening) return;

    // Hide previous results
    resultCard.classList.add('hidden');

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isListening = true;
        setVisualState('listening');
        stateLabel.textContent = 'LISTENING...';
        voiceIndicator.classList.remove('hidden');

        // Setup mic audio viz
        navigator.mediaDevices.getUserMedia({ audio: true }).then(setupAudioAnalyzer);
    };

    let finalTranscript = '';
    recognition.onresult = (e) => {
        finalTranscript = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) finalTranscript += e.results[i][0].transcript;
        }
        if (finalTranscript) stateLabel.textContent = finalTranscript.substring(0, 60).toUpperCase();
    };

    recognition.onend = () => {
        isListening = false;
        voiceIndicator.classList.add('hidden');

        if (finalTranscript.trim() && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'voice_input', text: finalTranscript }));
            stateLabel.textContent = 'TRANSMITTING TO META-LOOP...';
            setVisualState('reflecting');
        } else {
            setVisualState('idle');
            stateLabel.textContent = 'READY FOR LINK';
        }

        // Cleanup audio context
        if (audioCtx) audioCtx.close().catch(() => {});
    };

    recognition.onerror = (e) => {
        isListening = false;
        voiceIndicator.classList.add('hidden');
        stateLabel.textContent = `VOICE ERROR: ${e.error.toUpperCase()}`;
        setVisualState('idle');
    };

    recognition.start();
}

function speakResult(text) {
    // Truncate for TTS (avoid reading code blocks)
    const cleanText = text.replace(/```[\s\S]*?```/g, '(code block omitted)')
                          .replace(/[#*_`]/g, '')
                          .substring(0, 500);

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.05;
    utterance.pitch = 0.85;

    const voices = speechSynthesis.getVoices();
    const pref = voices.find(v => v.name.includes('Daniel') || v.name.includes('Samantha'));
    if (pref) utterance.voice = pref;

    utterance.onstart = () => setVisualState('speaking');
    utterance.onend = () => {
        setVisualState('idle');
        stateLabel.textContent = 'READY FOR LINK';
    };

    speechSynthesis.speak(utterance);
}

// Preload voices
speechSynthesis.getVoices();

// ═══════════════════════════════════════════
//  INTERACTION: Click the canvas to start voice
// ═══════════════════════════════════════════

canvas.addEventListener('click', () => {
    if (speechSynthesis.speaking) speechSynthesis.cancel();
    startListening();
});

// Dismiss result card on click
resultCard.addEventListener('click', () => {
    resultCard.classList.add('hidden');
    stateLabel.textContent = 'READY FOR LINK';
});
