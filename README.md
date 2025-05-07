# Meic Cymru Chatbot

A role-playing chatbot that simulates conversations between young people and Meic Cymru helpline advisors. The chatbot uses Google's Gemini AI to create realistic interactions and provides feedback on advisor performance.

## Features

- Role-playing personas with diverse backgrounds and issues
- Realistic Welsh cultural context and references
- Performance evaluation system
- PDF export of conversations and feedback
- Interactive chat interface

## Setup

1. Clone the repository:
```bash
git clone [your-repository-url]
cd gemini_chatbot
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `config.py` file with your Gemini API key:
```python
GEMINI_API_KEY = 'your-api-key-here'
```

5. Run the application:
```bash
python app.py
```

6. Open http://127.0.0.1:5000 in your browser

## Usage

1. Start a chat with a randomly generated persona
2. Respond as a Meic Cymru helpline advisor
3. Click "End Chat" to receive feedback
4. Download the conversation and feedback as PDF

## Requirements

- Python 3.8+
- Flask
- Google Generative AI
- ReportLab
- Other dependencies listed in requirements.txt