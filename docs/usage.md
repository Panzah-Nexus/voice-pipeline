# Usage Guide

This guide explains how to use the air-gapped voice pipeline system effectively once it's deployed on RunPod.

## 🎯 Daily Workflow

1.  **Start Your RunPod Pod**: Ensure your configured pod is running on RunPod.
2.  **Get the WebSocket URL**: Open your pod's `/connect` endpoint to get the current `ws_url`.
3.  **Configure the Client**:
    -   Navigate to the web client directory: `cd client/websocket-client`.
    -   Update the `VITE_WS_URL` in your `.env` file with the new URL.
4.  **Run the Client**:
    -   Run `npm run dev`.
    -   Open `http://localhost:5173` in your browser.
5.  **Start a Conversation**: Click the "Start" button and begin speaking.
6.  **Stop the Pod**: When you are finished, stop your RunPod pod to save costs.

## 🎙️ Speaking Tips

-   **Clear Articulation**: Speak at a normal, conversational pace.
-   **Quiet Environment**: Minimize background noise for best results.
-   **Natural Speech**: The system is designed for conversational language, not robotic commands.
-   **Turn-Taking**: You can speak whenever you want. The pipeline supports quick turn-taking and interruption.

## 💬 Conversation Examples

The `UltravoxWithContextService` remembers previous parts of the conversation.

### Contextual Follow-up
```
You: "What are the main benefits of using an air-gapped system for AI?"
AI: "The main benefits are data privacy, as your information never leaves the secure environment, and enhanced security because it's isolated from external networks."

You: "Can you elaborate on the first point you made?"
AI: "Certainly. Regarding data privacy, since all processing happens on your private RunPod instance, there is no risk of your voice data being stored or analyzed by third-party API providers, which is crucial for sensitive applications."
```

## ⚙️ Configuration Options

### TTS Voice Selection (Server-Side)
You can change the `KokoroTTSService` voice by setting the `KOKORO_VOICE_ID` environment variable in your RunPod template.

Example in RunPod Environment Variables:
-   **Key**: `KOKORO_VOICE_ID`
-   **Value**: `en_US-lessac-medium` (or another desired voice)

## 📊 Monitoring Your Session

Your client web interface should provide status indicators to keep you informed:
-   `Connecting...`: Attempting to establish the WebSocket connection.
-   `Connected`: Connection successful and ready for audio.
-   `Listening...`: Actively capturing audio from your microphone.
-   `Thinking...`: Your speech is being analyzed by the AI on the server.
-   `Error`: A connection or processing error has occurred.

The primary performance indicator you will notice is the **round-trip time**: the delay between when you stop speaking and when the AI starts responding. On an NVIDIA L4, this should be very low (typically under 1.5 seconds).

## 🚫 Limitations

-   **No Real-Time Internet Access**: The air-gapped design means the AI cannot access live information from the web (e.g., current news, weather).
-   **Context Window**: The AI remembers the most recent portion of the conversation (e.g., the last 20 messages).
-   **Cold Starts**: The very first time you connect to a freshly started pod, there may be a one-time delay while the models are loaded into GPU memory. Subsequent connections will be much faster. 