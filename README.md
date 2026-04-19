# Nomad2.0

NOMAD is an AR HUD designed for real time risk and quality detection using computer vision and a large multimodal model. It uses streamlit for the interface, webrtc for low latency video streaming, and the Groq LLama 4 Scout model for quick visual inferences. 

The issue we're solving is SDG 10 (Reduced Inequalities). Many people around the world face problems due to their inability to understand different languages and surviving in ddifferent areas of the world, like immigrants and tourists. It's a proven statistic that almost 40% of people in America have responded to surveys saying tahat their English isn't the best, and this number is even higher for brand new tourists or immigrants who know nothing about the country. Nomad solves this by using the quick, continuous flow where the user can scan any item and it will return a description of the item, name of the item, and how to request the item (to someone like an employee) all in the user's chosen language. This product is meant to enhance the user's experience in a new country where they don't know much about the language or the different products sold in stores. It will help reduce inequalities by eliminating language barriers between different groups of people. 

Nomad is very relevant to this topic due to its clean, elegant solution to a massive problem. Nomad doesn't seek to solve 30 minor problems, it resolves the 1 major problem; the language barrier. Though Nomad works very well, there are some limitations. Firstly, we cannot access every single language on Earth, some languages just aren't fully available, but we seek to add as many languages as possible to help as many people as possible. A future addition we could add would be to address more people in general, like instead of just immigrants and tourists, we could add features like hearing aid devices for blind people. 

Most of our engineering process was taken up by iterative testing as we needed to adjust the prompt and AR availability through many tests so we could see what went wrong and what went right. One of the major challenges we overcame was the api requests, where we had to make a stability feature that scans the product instead of just sending a request every 1 or 2 seconsd to make sure we don't hit the rate limit quickly.

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


