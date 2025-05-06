# Gemini Chatbot

A simple web-based chatbot application using Google's Gemini AI API.

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
   You can get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Running the Application

1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to `http://localhost:5000`

## Features

- Modern, responsive chat interface
- Real-time message exchange
- Error handling and user feedback
- Typing indicators

## Requirements

- Python 3.7+
- Flask
- google-generativeai
- python-dotenv