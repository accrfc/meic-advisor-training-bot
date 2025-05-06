from flask import Flask, render_template, request, jsonify, session, send_file
import google.generativeai as genai
import os
import random
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session

# Configure Flask to allow all connections
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("No GEMINI_API_KEY found in environment variables")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Possible themes and locations
THEMES = {
    "money": [
        {
            "issue": "struggling with bills at home",
            "outcome": "get help with budgeting and find ways to reduce household expenses"
        },
        {
            "issue": "can't afford school trips",
            "outcome": "find funding options or alternative ways to participate in school activities"
        },
        {
            "issue": "worried about family's financial situation",
            "outcome": "get advice on how to support my family and manage my own finances"
        }
    ],
    "relationships": [
        {
            "issue": "problems with friends at school",
            "outcome": "learn how to handle conflicts and rebuild friendships"
        },
        {
            "issue": "family arguments at home",
            "outcome": "find ways to communicate better with my family and reduce arguments"
        },
        {
            "issue": "feeling left out of social groups",
            "outcome": "build confidence to make new friends and feel included"
        }
    ],
    "mental health": [
        {
            "issue": "feeling really anxious lately",
            "outcome": "learn coping strategies and find ways to manage my anxiety"
        },
        {
            "issue": "struggling with low mood",
            "outcome": "get support and find activities that help improve my mood"
        },
        {
            "issue": "having panic attacks",
            "outcome": "learn techniques to prevent and manage panic attacks"
        }
    ],
    "bullying": [
        {
            "issue": "being picked on at school",
            "outcome": "get help to stop the bullying and feel safe at school"
        },
        {
            "issue": "receiving mean messages online",
            "outcome": "learn how to handle online bullying and protect my privacy"
        },
        {
            "issue": "excluded from friendship groups",
            "outcome": "find ways to rebuild friendships or make new friends"
        }
    ],
    "family": [
        {
            "issue": "parents arguing a lot",
            "outcome": "find ways to cope with family stress and improve home life"
        },
        {
            "issue": "difficult relationship with step-parent",
            "outcome": "build a better relationship with my step-parent"
        },
        {
            "issue": "feeling ignored at home",
            "outcome": "get help to communicate better with my family"
        }
    ],
    "school": [
        {
            "issue": "falling behind in lessons",
            "outcome": "get extra help with my studies and improve my grades"
        },
        {
            "issue": "problems with a teacher",
            "outcome": "resolve conflicts with my teacher and improve our relationship"
        },
        {
            "issue": "finding exams stressful",
            "outcome": "learn study techniques and ways to manage exam stress"
        }
    ]
}

LOCATIONS = [
    "Swansea", "Cardiff", "Newport", "Wrexham", "Bangor", "Aberystwyth",
    "Carmarthen", "Merthyr Tydfil", "Rhyl", "Llanelli", "Porthmadog",
    "Brecon", "Abergavenny", "Caernarfon", "Haverfordwest", 'Ponty', 'Merthyr', 'Ynysybwl', 'hay-on-wye'
]

# Welsh cultural elements
WELSH_REFERENCES = {
    "schools": [
        "Ysgol Gyfun", "Welsh-medium school", "English-medium school with Welsh lessons",
        "bilingual school", "Eisteddfod participant", "Urdd member"
    ],
    "interests": [
        "rugby", "football", "Welsh choir", "Welsh language learning",
        "traditional Welsh dancing", "Eisteddfod competitions", "Welsh literature",
        "Welsh history", "local Welsh festivals"
    ],
    "family": [
        "Welsh-speaking family", "mixed language household", "first language Welsh",
        "learning Welsh as second language", "traditional Welsh family",
        "modern Welsh family"
    ]
}

# Communication styles
COMMUNICATION_STYLES = [
    {
        "style": "hesitant",
        "traits": "very brief messages, takes time to open up, needs encouragement",
        "example": "hi... not sure if i should say this"
    },
    {
        "style": "quiet",
        "traits": "short, simple messages, may need prompting to share more",
        "example": "i need help with something"
    },
    {
        "style": "nervous",
        "traits": "brief messages with uncertainty, may use ellipses",
        "example": "um... can i talk about something?"
    },
    {
        "style": "shy",
        "traits": "minimal responses, needs gentle encouragement",
        "example": "yeah... it's hard to talk about"
    },
    {
        "style": "uncertain",
        "traits": "short messages with questions, unsure how to express themselves",
        "example": "is this the right place to talk about... stuff?"
    }
]

# Gender identities
GENDER_IDENTITIES = [
    {"identity": "boy", "pronouns": "he/him"},
    {"identity": "girl", "pronouns": "she/her"},
    {"identity": "non-binary person", "pronouns": "they/them"},
    {"identity": "trans boy", "pronouns": "he/him"},
    {"identity": "trans girl", "pronouns": "she/her"},
    {"identity": "genderfluid person", "pronouns": "they/them"},
    {"identity": "agender person", "pronouns": "they/them"}
]

# School/college scenarios
EDUCATION_SCENARIOS = [
    {
        "type": "secondary_school",
        "details": "attending a local comprehensive school",
        "challenges": ["exams", "homework", "school social life", "teachers"]
    },
    {
        "type": "sixth_form",
        "details": "studying A-levels or equivalent",
        "challenges": ["university applications", "increased workload", "future planning"]
    },
    {
        "type": "college",
        "details": "studying vocational courses",
        "challenges": ["work placements", "practical skills", "career focus"]
    },
    {
        "type": "apprenticeship",
        "details": "combining work and study",
        "challenges": ["work-life balance", "professional environment", "skill development"]
    }
]

def generate_persona():
    age = random.randint(10, 25)
    gender = random.choice(GENDER_IDENTITIES)
    location = random.choice(LOCATIONS)
    theme_category = random.choice(list(THEMES.keys()))
    scenario = random.choice(THEMES[theme_category])
    communication = random.choice(COMMUNICATION_STYLES)
    education = random.choice(EDUCATION_SCENARIOS)
    welsh_school = random.choice(WELSH_REFERENCES["schools"])
    welsh_interest = random.choice(WELSH_REFERENCES["interests"])
    welsh_family = random.choice(WELSH_REFERENCES["family"])
    
    return {
        "age": age,
        "gender": gender,
        "location": location,
        "theme": theme_category,
        "issue": scenario["issue"],
        "outcome": scenario["outcome"],
        "communication": communication,
        "education": education,
        "welsh_school": welsh_school,
        "welsh_interest": welsh_interest,
        "welsh_family": welsh_family
    }

def get_system_prompt(persona):
    return f"""You are role-playing as a {persona['age']} year old {persona['gender']['identity']} from {persona['location']} 
who is contacting the Meic Cymru helpline.

Background:
- {persona['education']['details']}
- From a {persona['welsh_family']}
- Attends a {persona['welsh_school']}
- Interested in {persona['welsh_interest']}

Your situation:
- You are experiencing: {persona['issue']}
- Your desired outcome is: {persona['outcome']}
- You should NOT immediately reveal your desired outcome
- Let the advisor help you work through your feelings and find solutions

As the young person:
1. Use {persona['gender']['pronouns']} pronouns
2. Keep messages short and natural (1-2 sentences max)
3. Start by explaining your issue but don't share everything at once
4. Use informal language appropriate for your age
5. Use some Welsh words or phrases occasionally (but keep it natural)
6. Reference your Welsh background and interests naturally
7. Consider your education context when discussing issues
8. If asked about your issue, share more details gradually
9. If asked how you're feeling, describe your emotions honestly
10. If asked about your background, mention your school, family, or interests
11. If given advice, respond to it and share your thoughts
12. If asked to elaborate, provide more details
13. NEVER repeat the same phrase or response
14. ALWAYS provide new information in each message
15. If the advisor helps you reach your desired outcome, you can say goodbye
16. Remember to be natural and human-like in your responses

Remember you are a young person seeking help, not a counselor or advisor.
Your responses should be brief and reflect the perspective and language of a young person in Wales.
Start by explaining your issue and then respond naturally to the advisor's questions."""

@app.route('/')
def home():
    # Generate a new persona and reset conversation history
    session['persona'] = generate_persona()
    session['system_prompt'] = get_system_prompt(session['persona'])
    session['conversation_history'] = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
            
        # Get the system prompt and conversation history from session
        system_prompt = session.get('system_prompt', '')
        conversation_history = session.get('conversation_history', [])
        
        if not system_prompt:
            # If somehow the session was lost, generate a new persona
            session['persona'] = generate_persona()
            session['system_prompt'] = get_system_prompt(session['persona'])
            system_prompt = session['system_prompt']
            conversation_history = []
        
        # Format the conversation history
        history_text = ""
        for msg in conversation_history:
            role = "Advisor" if msg['role'] == 'user' else "Young Person"
            history_text += f"{role}: {msg['content']}\n"
        
        # Combine system prompt, conversation history, and new message
        full_prompt = f"""{system_prompt}

Previous conversation:
{history_text}

Advisor: {user_message}
Young Person: """
        
        response = model.generate_content(full_prompt)
        
        if not response.text:
            return jsonify({'error': 'Empty response from Gemini API'}), 500
            
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": response.text})
        session['conversation_history'] = conversation_history
        
        return jsonify({'response': response.text})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': f'API Error: {str(e)}'}), 500

def analyze_conversation(conversation, persona):
    # Create a prompt for the AI to analyze the conversation
    analysis_prompt = f"""Analyze this conversation between a Meic Cymru helpline advisor and a {persona['age']} year old {persona['gender']['identity']} from {persona['location']} 
who is contacting about an issue related to {persona['theme']}.

Evaluate the advisor's performance in these areas:

1. Tone of Voice (0-100):
- Was the advisor friendly and approachable?
- Did they maintain a professional yet empathetic tone?
- Were they patient and understanding?

2. Engagement (0-100):
- Did the advisor actively listen to the young person?
- Did they ask appropriate follow-up questions?
- Did they allow the young person to express themselves fully?
- Did they show genuine interest in the young person's situation?

3. Resolution (0-100):
- Was the issue addressed effectively?
- Were appropriate solutions or next steps suggested?
- Was the conversation productive and focused?
- How quickly was the core issue identified and addressed?

4. Information Provided (0-100):
- Were relevant services or resources recommended?
- Was the information appropriate for the young person's location and situation?
- Were alternative options considered?
- Was the information clear and understandable?

For each category, provide:
1. A score (0-100)
2. Specific feedback on what was done well and what could be improved
3. Examples from the conversation to support your evaluation

Conversation:
{format_conversation(conversation)}

Provide your analysis in this exact format:
TONE_SCORE: [number]
TONE_FEEDBACK: [feedback]

ENGAGEMENT_SCORE: [number]
ENGAGEMENT_FEEDBACK: [feedback]

RESOLUTION_SCORE: [number]
RESOLUTION_FEEDBACK: [feedback]

INFORMATION_SCORE: [number]
INFORMATION_FEEDBACK: [feedback]

OVERALL_SCORE: [number]
OVERALL_FEEDBACK: [feedback]"""

    try:
        response = model.generate_content(analysis_prompt)
        return parse_analysis(response.text)
    except Exception as e:
        print(f"Error analyzing conversation: {str(e)}")
        return None

def format_conversation(conversation):
    formatted = ""
    for msg in conversation:
        role = "Advisor" if msg['role'] == 'user' else "Young Person"
        formatted += f"{role}: {msg['content']}\n\n"
    return formatted

def parse_analysis(analysis_text):
    scores = {
        'tone': {'score': 0, 'feedback': ''},
        'engagement': {'score': 0, 'feedback': ''},
        'resolution': {'score': 0, 'feedback': ''},
        'information': {'score': 0, 'feedback': ''},
        'overall': {'score': 0, 'feedback': ''}
    }
    
    current_section = None
    for line in analysis_text.split('\n'):
        line = line.strip()
        if line.startswith('TONE_SCORE:'):
            scores['tone']['score'] = int(line.split(':')[1].strip())
        elif line.startswith('TONE_FEEDBACK:'):
            scores['tone']['feedback'] = line.split(':', 1)[1].strip()
        elif line.startswith('ENGAGEMENT_SCORE:'):
            scores['engagement']['score'] = int(line.split(':')[1].strip())
        elif line.startswith('ENGAGEMENT_FEEDBACK:'):
            scores['engagement']['feedback'] = line.split(':', 1)[1].strip()
        elif line.startswith('RESOLUTION_SCORE:'):
            scores['resolution']['score'] = int(line.split(':')[1].strip())
        elif line.startswith('RESOLUTION_FEEDBACK:'):
            scores['resolution']['feedback'] = line.split(':', 1)[1].strip()
        elif line.startswith('INFORMATION_SCORE:'):
            scores['information']['score'] = int(line.split(':')[1].strip())
        elif line.startswith('INFORMATION_FEEDBACK:'):
            scores['information']['feedback'] = line.split(':', 1)[1].strip()
        elif line.startswith('OVERALL_SCORE:'):
            scores['overall']['score'] = int(line.split(':')[1].strip())
        elif line.startswith('OVERALL_FEEDBACK:'):
            scores['overall']['feedback'] = line.split(':', 1)[1].strip()
    
    return scores

@app.route('/end-chat', methods=['POST'])
def end_chat():
    try:
        conversation = request.json.get('conversation', [])
        if not conversation:
            return jsonify({'error': 'No conversation provided'}), 400
            
        persona = session.get('persona')
        if not persona:
            return jsonify({'error': 'No persona found'}), 400
            
        feedback = analyze_conversation(conversation, persona)
        if not feedback:
            return jsonify({'error': 'Failed to analyze conversation'}), 500
            
        return jsonify(feedback)
    except Exception as e:
        print(f"Error in end-chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

def create_pdf(conversation, feedback):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    story.append(Paragraph("Chat Conversation and Feedback", title_style))
    
    # Add conversation
    story.append(Paragraph("Conversation:", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # Create conversation table
    conv_data = [['Role', 'Message']]
    for msg in conversation:
        conv_data.append([msg['role'], msg['content']])
    
    conv_table = Table(conv_data, colWidths=[1.5*inch, 4.5*inch])
    conv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(conv_table)
    story.append(Spacer(1, 20))
    
    # Add feedback
    story.append(Paragraph("Feedback:", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # Create feedback table
    feedback_data = [
        ['Category', 'Score', 'Feedback'],
        ['Tone of Voice', feedback['tone']['score'], feedback['tone']['feedback']],
        ['Engagement', feedback['engagement']['score'], feedback['engagement']['feedback']],
        ['Resolution', feedback['resolution']['score'], feedback['resolution']['feedback']],
        ['Information Provided', feedback['information']['score'], feedback['information']['feedback']],
        ['Overall', feedback['overall']['score'], feedback['overall']['feedback']]
    ]
    
    feedback_table = Table(feedback_data, colWidths=[2*inch, 1*inch, 3*inch])
    feedback_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(feedback_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/save-chat', methods=['POST'])
def save_chat():
    try:
        data = request.json
        conversation = data.get('conversation', [])
        feedback = data.get('feedback', {})
        
        if not conversation or not feedback:
            return jsonify({'error': 'No conversation or feedback provided'}), 400
            
        # Create PDF
        pdf_buffer = create_pdf(conversation, feedback)
        
        # Return PDF as download
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='chat-feedback.pdf'
        )
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Server will be available at http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True) 