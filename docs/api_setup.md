# API and Model Setup Guide

This guide covers the setup of the necessary API tokens and provides information on the models used in the voice pipeline.

## Required Token: Hugging Face

The only external credential you need is a **Hugging Face Access Token**. This token is used **only once** during the pod's initial startup to download the pre-trained Ultravox model from the Hugging Face Hub.

### 1. Create a Hugging Face Account
If you don't have one, sign up at [huggingface.co](https://huggingface.co/).

### 2. Generate an Access Token
1.  Navigate to your Hugging Face account settings: **[Settings → Access Tokens](https://huggingface.co/settings/tokens)**.
2.  Click **"New token"**, give it a name, and assign it the **`Read`** role.
3.  Copy the generated key (it starts with `hf_`).

### 3. Configure the Token in RunPod
This token must be provided to your RunPod pod as an environment variable. When configuring your pod, create a variable with the **Key** `HF_TOKEN` and paste your token as the **Value**.

The application code automatically looks for this `HF_TOKEN` environment variable to authenticate with Hugging Face.

## Model Information

### STT + LLM: Ultravox
-   **Service**: `UltravoxWithContextService`
-   **Model**: `fixie-ai/ultravox-v0_5-llama-3_1-8b`
-   **Description**: An 8-billion parameter model that processes audio directly and maintains conversation context. It is highly performant on an NVIDIA L4 GPU.

### Text-to-Speech: Kokoro
-   **Service**: `KokoroTTSService`
-   **Description**: An offline neural TTS engine. The specific voice can be configured via the `KOKORO_VOICE_ID` environment variable in RunPod.
-   **Default Voice**: `af_bella`

## Security Best Practices

-   ✅ Provide the `HF_TOKEN` as a RunPod environment variable.
-   ❌ **Never** hardcode your token directly in the source code.
-   ❌ **Never** commit your token to a Git repository.
-   ✅ Ensure your local `.env` files are listed in your `.gitignore` file.
