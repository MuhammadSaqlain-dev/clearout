import logging
import sys
import time
from typing import Optional
import requests
import streamlit as st
from streamlit_chat import message
import cloudinary
import cloudinary.uploader

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=log_format, stream=sys.stdout, level=logging.INFO)

# Cloudinary configuration
cloudinary.config(
  cloud_name="darkdegwd", 
  api_key="345662779321261", 
  api_secret="MYv7ImXfjyc24DvTbMJS_2IISL0"
)

BASE_API_URL = "https://musaqlain-langflow-hackathon-clearout.hf.space/api/v1/run"
FLOW_ID = "3e615e54-b310-43a5-a2d0-e9b671b0e6da"
BASE_AVATAR_URL = (
    "https://raw.githubusercontent.com/garystafford-aws/static-assets/main/static"
)

uploaded_img_url = None


def upload_image_to_cloudinary(image_file):
    try:
        response = cloudinary.uploader.upload(image_file)
        return response['secure_url']
    except Exception as e:
        st.error(f"Error uploading image: {e}")
        return None


def main():
    st.set_page_config(page_title="Clearout")

    st.markdown("##### Welcome to the ClearOut")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message["avatar"]):
            st.write(message["content"])
    
    # Ensure uploaded image URL is initialized in session state
    if "uploaded_img_url" not in st.session_state:
        st.session_state.uploaded_img_url = None

    if prompt := st.chat_input("I'm your Noble friend, how may I help you to dispose things?"):
        # Add user message to chat history
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt,
                "avatar": f"{BASE_AVATAR_URL}/people-64px.png",
            }
        )
        # Display user message in chat message container
        with st.chat_message(
            "user",
            avatar=f"{BASE_AVATAR_URL}/people-64px.png",
        ):
            st.write(prompt)

        # Display assistant response in chat message container
        with st.chat_message(
            "assistant",
            avatar=f"{BASE_AVATAR_URL}/bartender-64px.png",
        ):
            message_placeholder = st.empty()
            with st.spinner(text="Thinking..."):
                assistant_response = generate_response(prompt)
                message_placeholder.write(assistant_response)
        # Add assistant response to chat history
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": assistant_response,
                "avatar": f"{BASE_AVATAR_URL}/bartender-64px.png",
            }
        )
    
    # Call the file upload component
    file_upload_component()


def file_upload_component():
    global uploaded_img_url  # Declare the variable as global
    
    st.markdown("### Upload an Image")
    
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        
        if st.button("Upload to Cloudinary"):
            with st.spinner("Uploading..."):
                image_url = upload_image_to_cloudinary(uploaded_file)
                st.session_state.uploaded_img_url = image_url


def run_flow(inputs: dict, flow_id: str, tweaks: Optional[dict] = None) -> dict:
    api_url = f"{BASE_API_URL}/{flow_id}"

    payload = {"inputs": inputs}

    if tweaks:
        payload["tweaks"] = tweaks

    response = requests.post(api_url, json=payload)
    
    return response.json()


def generate_response(prompt):
    logging.info(f"question: {prompt}")
    inputs = {"question": prompt}
    
    # Dynamically create TWEAKS dictionary
    tweaks = {
        "ChatInput-irjw6": {
            "input_value": prompt,
            "sender": "User",
            "sender_name": "User",
            "session_id": "",
            "store_message": True
        },
    }

    if st.session_state.uploaded_img_url:
        tweaks["FileUploadComponent-Xsq0d"] = {
            "AIMLApiKey": "1fd6b15558b241f5822130237ea84dba",
            "MaxTokens": 300,
            "model": "gpt-4o",
            "prompt": "Name the items in the image",
            "uploaded_file": st.session_state.uploaded_img_url
        }

    response = run_flow(inputs, flow_id=FLOW_ID, tweaks=tweaks)

    try:
        logging.info(f"answer: {response['outputs'][0]['outputs'][0]['results']['message']['data']['text']}")
        return response['outputs'][0]['outputs'][0]['results']['message']['data']['text']
    except Exception as exc:
        logging.error(f"error: {response}")
        return "Sorry, there was a problem finding an answer for you."


if __name__ == "__main__":
    main()
