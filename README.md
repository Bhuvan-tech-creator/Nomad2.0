# Nomad2.0

NOMAD is an AR HUD designed for real time risk and quality detection using computer vision and a large multimodal model. It uses streamlit for the interface, webrtc for low latency video streaming, and the Groq LLama 4 Scout model for quick visual inferences. 

# Architecture and Data Flow

1. Browser requests camera access.
2. Local processing: frames are downsampled and onverted to grayscale, a stability check is in place (1.5 seconds) before the image gets transferred to the LMM to limit the number of accidental requests being sent.
3. Inference: once stable, the frame is compressed and encoded. Then, the payload is sent to Groq's Llama 4 Scout model with a comprehensive system prompt.
4. Localization: The JSON output from Llama 4 is passed through the Google Translate API to match the user's preferred language.
5. Augmentation: Results are drawn onto the frame using Pillow.

# Dependencies

streamlit-webrtc
opencv-python
groq
Pillow (PIL)
deep-translator

# Deployment Instructions

Create a .env file in the root directory

GROQ_API_KEY = *key here*

Then, run these commands in terminal:

pip install -r requirements.txt
streamlit run main.py


