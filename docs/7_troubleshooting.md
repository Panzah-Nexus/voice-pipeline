# 7. Troubleshooting

This guide provides solutions to common errors and issues you might encounter while working with the voice pipeline.

---

### 1. Error: `Could not find an enabled CUDA execution provider.`

*   **Symptom:** The application fails to start, and logs show an error related to `onnxruntime` not finding a CUDA provider.
*   **Cause:** This typically means that the NVIDIA drivers or the NVIDIA Container Toolkit are not set up correctly, so the Docker container cannot access the host's GPU.
*   **Solution:**
    1.  **Verify NVIDIA Drivers:** Ensure you have the correct NVIDIA drivers installed on your host machine.
    2.  **Install NVIDIA Container Toolkit:** Follow the [official installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) for your Linux distribution.
    3.  **Use `--gpus all`:** When running `docker run`, make sure you include the `--gpus all` flag to expose the GPU devices to the container.

---

### 2. Error: `TTS subprocess terminated unexpectedly.`

*   **Symptom:** The pipeline runs, but no audio is produced, and an error about the TTS sub-process is logged. Checking the container logs might reveal an error from `src/kokoro/tts_subprocess_server.py`.
*   **Cause:** This is a generic error that can have several causes related to the isolated TTS environment.
*   **Solution:**
    1.  **Check Model Paths:** Verify that the paths to the Kokoro model and voices files in your `.env` file (`KOKORO_MODEL_PATH`, `KOKORO_VOICES_PATH`) are correct and that the files exist.
    2.  **Check Python Path:** Ensure `KOKORO_PYTHON_PATH` points to the correct Python executable in the TTS virtual environment (`/venv/tts/bin/python`).
    3.  **Run Manually:** For deeper debugging, you can execute the sub-process server directly inside the running container to see more detailed errors:
        ```bash
        # Inside the container
        /venv/tts/bin/python /app/src/kokoro/tts_subprocess_server.py \
          --model-path /path/to/model.onnx \
          --voices-path /path/to/voices.bin \
          --debug
        ```

---

### 3. Error: `JSON line too long` or `Invalid JSON`

*   **Symptom:** An error related to JSON decoding appears in the logs, originating from the `KokoroSubprocessTTSService`.
*   **Cause:** This error occurs if the TTS sub-process sends a malformed or excessively long line of JSON to the parent process. This should be rare due to the built-in 16KB chunking mechanism.
*   **Solution:**
    1.  **Check for Custom Modifications:** If you have modified the TTS sub-process code (`tts_subprocess_server.py`), ensure you have not changed the audio chunking logic (`MAX_RAW_BYTES`).
    2.  **Inspect Logs:** Enable debug logging (`--log-level DEBUG`) to see the raw messages being passed between the processes, which can help identify the source of the malformed data.

---

### 4. Error: `Frame is not JSON serializable`

*   **Symptom:** The pipeline fails with a `TypeError` indicating that a `pipecat` frame object cannot be serialized to JSON.
*   **Cause:** This typically happens in custom development when attempting to put a non-serializable object (like a complex class instance) into a frame that needs to be transported or logged.
*   **Solution:**
    1.  **Review Custom Frames:** If you have created custom `pipecat` frames, ensure all data you store in them is JSON-serializable (e.g., strings, numbers, lists, dicts).
    2.  **Check `user_data`:** Be cautious about what you store in the `user_data` dictionaries of services. Only add data that can be safely serialized. 