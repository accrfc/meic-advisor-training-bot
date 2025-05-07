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
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session

# Configure Flask to allow all connections
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Load environment variables
load_dotenv()
print("Environment variables loaded")
print(f"GEMINI_API_KEY present: {'GEMINI_API_KEY' in os.environ}")

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Possible themes and locations
THEMES = {
    "money": [
        {
            "issue": "struggling with bills at home",
            "outcome": "get help with budgeting and find ways to reduce household expenses",
            "details": "Parents are working multiple jobs but still struggling to make ends meet. Worried about having to move schools if we can't afford the rent."
        },
        {
            "issue": "can't afford school trips",
            "outcome": "find funding options or alternative ways to participate in school activities",
            "details": "All my friends are going on the school trip to France but my family can't afford it. Feeling left out and embarrassed."
        },
        {
            "issue": "worried about family's financial situation",
            "outcome": "get advice on how to support my family and manage my own finances",
            "details": "Parents are arguing about money all the time. I want to help but don't know how. Thinking about getting a part-time job."
        },
        {
            "issue": "pressure to buy expensive things",
            "outcome": "learn how to handle peer pressure and make responsible financial decisions",
            "details": "Friends all have the latest phones and clothes. Feeling pressured to keep up but know my family can't afford it."
        }
    ],
    "relationships": [
        {
            "issue": "problems with friends at school",
            "outcome": "learn how to handle conflicts and rebuild friendships",
            "details": "My best friend has started hanging out with a new group and is ignoring me. Feeling hurt and lonely."
        },
        {
            "issue": "family arguments at home",
            "outcome": "find ways to communicate better with my family and reduce arguments",
            "details": "Constant arguments with parents about my future choices. They want me to go to university but I'm not sure."
        },
        {
            "issue": "feeling left out of social groups",
            "outcome": "build confidence to make new friends and feel included",
            "details": "Moved to a new school and finding it hard to make friends. Everyone seems to have their own groups already."
        },
        {
            "issue": "romantic relationship problems",
            "outcome": "get advice on healthy relationships and boundaries",
            "details": "First serious relationship and not sure if it's healthy. Partner is very controlling of who I can see."
        },
        {
            "issue": "online friendship issues",
            "outcome": "learn how to maintain healthy online relationships and set boundaries",
            "details": "Made friends online but they're pressuring me to share personal information and photos."
        }
    ],
    "mental health": [
        {
            "issue": "feeling really anxious lately",
            "outcome": "learn coping strategies and find ways to manage my anxiety",
            "details": "Getting panic attacks before exams and social situations. Can't sleep properly and always worrying."
        },
        {
            "issue": "struggling with low mood",
            "outcome": "get support and find activities that help improve my mood",
            "details": "Feeling down all the time, no energy to do things I used to enjoy. Friends are worried about me."
        },
        {
            "issue": "having panic attacks",
            "outcome": "learn techniques to prevent and manage panic attacks",
            "details": "Started having panic attacks in crowded places. Scared to go to school or social events."
        },
        {
            "issue": "stress about future",
            "outcome": "develop strategies to manage stress and make decisions about the future",
            "details": "Overwhelmed with pressure to choose a career path. Don't know what I want to do and everyone keeps asking."
        },
        {
            "issue": "body image concerns",
            "outcome": "build positive body image and develop healthy habits",
            "details": "Feeling self-conscious about my appearance. Social media makes me feel worse about how I look."
        }
    ],
    "bullying": [
        {
            "issue": "being picked on at school",
            "outcome": "get help to stop the bullying and feel safe at school",
            "details": "Group of older students keep making fun of me and spreading rumors. Scared to tell teachers."
        },
        {
            "issue": "receiving mean messages online",
            "outcome": "learn how to handle online bullying and protect my privacy",
            "details": "Getting anonymous messages on social media. They know personal things about me and I'm scared."
        },
        {
            "issue": "excluded from friendship groups",
            "outcome": "find ways to rebuild friendships or make new friends",
            "details": "Friends have started a group chat without me and are ignoring me at school. Don't know what I did wrong."
        },
        {
            "issue": "cyberbullying in gaming",
            "outcome": "learn how to handle toxic behavior in online gaming",
            "details": "Getting harassed in online games. People are making threats and sharing my personal information."
        },
        {
            "issue": "workplace bullying",
            "outcome": "get advice on handling workplace harassment",
            "details": "Older colleagues at my part-time job are making inappropriate comments and excluding me from tasks."
        }
    ],
    "family": [
        {
            "issue": "parents arguing a lot",
            "outcome": "find ways to cope with family stress and improve home life",
            "details": "Parents fight constantly about money and other issues. Worried they might split up."
        },
        {
            "issue": "difficult relationship with step-parent",
            "outcome": "build a better relationship with my step-parent",
            "details": "New step-parent moved in and we don't get along. They're trying to parent me but I don't want them to."
        },
        {
            "issue": "feeling ignored at home",
            "outcome": "get help to communicate better with my family",
            "details": "Parents are always busy with work and my younger siblings. Feel like they don't have time for me."
        },
        {
            "issue": "cultural differences with family",
            "outcome": "bridge cultural gaps and maintain family relationships",
            "details": "Parents want me to follow traditional values but I want to live more like my friends. Causing lots of arguments."
        },
        {
            "issue": "caring for family members",
            "outcome": "balance caring responsibilities with personal life",
            "details": "Looking after my younger siblings while parents work. Missing out on school activities and social life."
        }
    ],
    "school": [
        {
            "issue": "falling behind in lessons",
            "outcome": "get extra help with my studies and improve my grades",
            "details": "Struggling to keep up with coursework. Teachers are putting pressure on me to do better."
        },
        {
            "issue": "problems with a teacher",
            "outcome": "resolve conflicts with my teacher and improve our relationship",
            "details": "Teacher keeps picking on me and making negative comments. Other students notice and it's embarrassing."
        },
        {
            "issue": "finding exams stressful",
            "outcome": "learn study techniques and ways to manage exam stress",
            "details": "Panic during exams and can't remember what I've learned. Worried about failing my GCSEs."
        },
        {
            "issue": "choosing subjects",
            "outcome": "make informed decisions about subject choices",
            "details": "Need to choose A-level subjects but not sure what I want to do. Parents have different ideas."
        },
        {
            "issue": "school attendance problems",
            "outcome": "address barriers to regular school attendance",
            "details": "Missing lots of school due to anxiety. Getting letters about attendance and worried about consequences."
        }
    ],
    "identity": [
        {
            "issue": "exploring gender identity",
            "outcome": "get support in understanding and expressing gender identity",
            "details": "Questioning my gender identity but scared to talk to family. Friends are supportive but don't know how to help."
        },
        {
            "issue": "coming out concerns",
            "outcome": "navigate coming out process safely",
            "details": "Want to come out to family but worried about their reaction. They make negative comments about LGBTQ+ people."
        },
        {
            "issue": "cultural identity conflicts",
            "outcome": "balance cultural heritage with personal identity",
            "details": "Feeling torn between family's cultural expectations and wanting to fit in with friends at school."
        },
        {
            "issue": "religious beliefs",
            "outcome": "reconcile personal beliefs with family expectations",
            "details": "Starting to question family's religious beliefs but scared to talk about it. Worried about being rejected."
        }
    ],
    "health": [
        {
            "issue": "eating habits",
            "outcome": "develop healthy relationship with food",
            "details": "Struggling with irregular eating patterns. Sometimes skip meals, sometimes eat too much when stressed."
        },
        {
            "issue": "sleep problems",
            "outcome": "improve sleep habits and energy levels",
            "details": "Can't sleep properly, always tired at school. Using phone late at night to avoid thinking about problems."
        },
        {
            "issue": "physical health concerns",
            "outcome": "address health concerns and access support",
            "details": "Having unexplained symptoms but scared to tell parents. Worried it might be serious."
        },
        {
            "issue": "substance use",
            "outcome": "get support for reducing or stopping substance use",
            "details": "Started using substances to cope with stress. Want to stop but finding it hard."
        }
    ]
}

LOCATIONS = [
    "Swansea", "Cardiff", "Newport", "Wrexham", "Bangor", "Aberystwyth",
    "Carmarthen", "Rhyl", "Llanelli", "Porthmadog", "Aberdare", "Ebbw Vale",
    "Brecon", "Abergavenny", "Caernarfon", "Haverfordwest", "Pontypridd", 
    "Merthyr", "Ynysybwl", "Hay-on-Wye", "Llandrindod Wells", "Llanidloes",
    "Aberdare", "Abercynon", "Aberkenfig", "Abertridwr", "Llandovery",
    "Penarth", "Porthcawl", "Bridgend", "Tenby", "St. Clears", "St. Davids",
    "Conwy", "Llandgollen", "Crickhowell", "Llandudno", "Chepstow", "Pontypool",
    "Aberavon", "Aberdulais", "Aberfan", "Abercwmboi", "Neath", "Port Talbot", 
    "Caernarfon", "Abergele", "Colwyn Bay", "Llanberis", "Harlech", "Portmeirion",
    "Ruthin", "Machynlleth", "Dolgellau", "Holyhead", "Blaenau Ffestiniog", "Bala"
]

# Enhanced Welsh cultural elements
WELSH_REFERENCES = {
    "schools": [
        "Ysgol Gyfun", "Welsh-medium school", "English-medium school with Welsh lessons",
        "bilingual school", "Eisteddfod participant", "Urdd member",
        "Welsh language stream", "Welsh heritage school", "Welsh culture club member",
        "Welsh literature student", "Welsh history enthusiast", "Welsh music group member"
    ],
    "interests": [
        "rugby", "football", "Welsh choir", "Welsh language learning",
        "traditional Welsh dancing", "Eisteddfod competitions", "Welsh literature",
        "Welsh history", "local Welsh festivals", "Welsh folk music",
        "Welsh art and crafts", "Welsh poetry", "Welsh mythology",
        "Welsh sports", "Welsh cooking", "Welsh environmental projects",
        "Welsh community events", "Welsh media", "Welsh politics",
        "Welsh cultural heritage"
    ],
    "family": [
        "Welsh-speaking family", "mixed language household", "first language Welsh",
        "learning Welsh as second language", "traditional Welsh family",
        "modern Welsh family", "Welsh heritage family", "Welsh cultural family",
        "Welsh community family", "Welsh diaspora family",
        "Welsh-English bilingual family", "Welsh cultural traditions",
        "Welsh family values", "Welsh family history"
    ],
    "communities": [
        "Welsh language community", "Welsh cultural society", "Welsh youth group",
        "Welsh sports club", "Welsh music group", "Welsh dance group",
        "Welsh literature circle", "Welsh history society", "Welsh environmental group",
        "Welsh community center", "Welsh cultural events", "Welsh heritage group"
    ]
}

# Youth interests (non-Welsh specific)
YOUTH_INTERESTS = [
    {
        "category": "Digital & Online",
        "interests": [
            "gaming", "social media", "streaming content", "online influencers",
            "memes & online humor", "podcasts", "photography & videography",
            "digital art", "online communities", "virtual reality"
        ]
    },
    {
        "category": "Creative & Arts",
        "interests": [
            "music", "creative arts", "crafting & DIY", "reading", "writing",
            "drawing", "painting", "digital design", "animation", "filmmaking"
        ]
    },
    {
        "category": "Physical & Social",
        "interests": [
            "sports & fitness", "fashion & style", "socializing", "dance",
            "outdoor activities", "team sports", "individual sports", "fitness trends",
            "street fashion", "makeup & beauty"
        ]
    },
    {
        "category": "Learning & Development",
        "interests": [
            "learning new skills", "travel & exploration", "mental wellbeing",
            "social & environmental issues", "collecting", "cooking & baking",
            "language learning", "coding & technology", "science experiments",
            "history & culture"
        ]
    }
]

# Enhanced communication styles
COMMUNICATION_STYLES = [
    {
        "style": "hesitant",
        "traits": "very brief messages, takes time to open up, needs encouragement",
        "example": "hi... not sure if i should say this",
        "characteristics": ["shy", "uncertain", "needs reassurance", "careful with words"]
    },
    {
        "style": "quiet",
        "traits": "short, simple messages, may need prompting to share more",
        "example": "i need help with something",
        "characteristics": ["reserved", "thoughtful", "observant", "prefers listening"]
    },
    {
        "style": "nervous",
        "traits": "brief messages with uncertainty, may use ellipses",
        "example": "um... can i talk about something?",
        "characteristics": ["anxious", "worried", "seeks validation", "overthinks"]
    },
    {
        "style": "shy",
        "traits": "minimal responses, needs gentle encouragement",
        "example": "yeah... it's hard to talk about",
        "characteristics": ["introverted", "self-conscious", "needs time", "careful"]
    },
    {
        "style": "uncertain",
        "traits": "short messages with questions, unsure how to express themselves",
        "example": "is this the right place to talk about... stuff?",
        "characteristics": ["doubtful", "seeking guidance", "needs clarity", "cautious"]
    },
    {
        "style": "direct",
        "traits": "clear and straightforward, gets to the point",
        "example": "I need help with bullying at school",
        "characteristics": ["confident", "assertive", "practical", "solution-focused"]
    },
    {
        "style": "emotional",
        "traits": "expressive, shares feelings openly",
        "example": "I'm really upset about what's happening",
        "characteristics": ["sensitive", "expressive", "needs empathy", "open"]
    },
    {
        "style": "formal",
        "traits": "polite and structured, uses proper language",
        "example": "I would like to discuss a personal matter",
        "characteristics": ["respectful", "organized", "careful", "professional"]
    }
]

# Enhanced gender identities
GENDER_IDENTITIES = [
    {"identity": "boy", "pronouns": "he/him", "characteristics": ["masculine", "male", "man"]},
    {"identity": "girl", "pronouns": "she/her", "characteristics": ["feminine", "female", "woman"]},
    {"identity": "non-binary person", "pronouns": "they/them", "characteristics": ["gender-neutral", "non-binary", "enby"]},
    {"identity": "trans boy", "pronouns": "he/him", "characteristics": ["transmasculine", "trans male", "trans man"]},
    {"identity": "trans girl", "pronouns": "she/her", "characteristics": ["transfeminine", "trans female", "trans woman"]},
    {"identity": "genderfluid person", "pronouns": "they/them", "characteristics": ["fluid", "flexible", "changing"]},
    {"identity": "agender person", "pronouns": "they/them", "characteristics": ["genderless", "neutral", "unaffiliated"]},
    {"identity": "genderqueer person", "pronouns": "they/them", "characteristics": ["queer", "non-conforming", "unique"]}
]

# Enhanced education scenarios
EDUCATION_SCENARIOS = [
    {
        "type": "secondary_school",
        "details": "attending a local comprehensive school",
        "challenges": ["exams", "homework", "school social life", "teachers"],
        "characteristics": ["GCSE student", "teenager", "school-focused", "peer-oriented"]
    },
    {
        "type": "sixth_form",
        "details": "studying A-levels or equivalent",
        "challenges": ["university applications", "increased workload", "future planning"],
        "characteristics": ["post-16 student", "academic", "future-focused", "independent"]
    },
    {
        "type": "college",
        "details": "studying vocational courses",
        "challenges": ["work placements", "practical skills", "career focus"],
        "characteristics": ["vocational student", "hands-on", "career-oriented", "practical"]
    },
    {
        "type": "apprenticeship",
        "details": "combining work and study",
        "challenges": ["work-life balance", "professional environment", "skill development"],
        "characteristics": ["working student", "professional", "balanced", "developing"]
    },
    {
        "type": "special_education",
        "details": "attending a specialist school",
        "challenges": ["learning support", "social integration", "individual needs"],
        "characteristics": ["supported learning", "individualized", "inclusive", "focused"]
    },
    {
        "type": "home_education",
        "details": "learning at home",
        "challenges": ["socialization", "structure", "resources"],
        "characteristics": ["independent learner", "flexible", "self-directed", "family-oriented"]
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
    welsh_community = random.choice(WELSH_REFERENCES["communities"])
    
    # Select random interest category and interest
    interest_category = random.choice(YOUTH_INTERESTS)
    youth_interest = random.choice(interest_category["interests"])
    
    return {
        "age": age,
        "gender": gender,
        "location": location,
        "theme": theme_category,
        "issue": scenario["issue"],
        "outcome": scenario["outcome"],
        "details": scenario["details"],
        "communication": communication,
        "education": education,
        "welsh_school": welsh_school,
        "welsh_interest": welsh_interest,
        "welsh_family": welsh_family,
        "welsh_community": welsh_community,
        "youth_interest_category": interest_category["category"],
        "youth_interest": youth_interest
    }

def get_system_prompt(persona):
    return f"""You are role-playing as a {persona['age']} year old {persona['gender']['identity']} from {persona['location']} 
who is contacting the Meic Cymru helpline.

Background:
- {persona['education']['details']}
- From a {persona['welsh_family']}
- Attends a {persona['welsh_school']}
- Interested in {persona['welsh_interest']} (Welsh culture)
- Also interested in {persona['youth_interest']} ({persona['youth_interest_category']})

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

First, provide a brief summary of the conversation in 2-3 sentences.

Then, provide information about the young person in this format:
ABOUT_YOUNG_PERSON: [Include age, gender, location, education, Welsh background, and the specific issue they were dealing with]

Then evaluate the advisor's performance in these areas:

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
CONVERSATION_SUMMARY: [2-3 sentence summary]

ABOUT_YOUNG_PERSON: [Details about the young person]

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
        'conversation_summary': '',
        'about_young_person': '',
        'tone': {'score': 0, 'feedback': ''},
        'engagement': {'score': 0, 'feedback': ''},
        'resolution': {'score': 0, 'feedback': ''},
        'information': {'score': 0, 'feedback': ''},
        'overall': {'score': 0, 'feedback': ''}
    }
    
    current_section = None
    for line in analysis_text.split('\n'):
        line = line.strip()
        if line.startswith('CONVERSATION_SUMMARY:'):
            scores['conversation_summary'] = line.split(':', 1)[1].strip()
        elif line.startswith('ABOUT_YOUNG_PERSON:'):
            scores['about_young_person'] = line.split(':', 1)[1].strip()
        elif line.startswith('TONE_SCORE:'):
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
            
        # Add persona information to the response
        feedback['persona'] = persona
            
        return jsonify(feedback)
    except Exception as e:
        print(f"Error in end-chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

def create_pdf(conversation, feedback):
    try:
        buffer = BytesIO()
        # Add margins to the document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=50,
            rightMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        styles = getSampleStyleSheet()
        story = []
        
        # Get current date and time
        current_datetime = datetime.now().strftime("%d %B %Y, %H:%M")
        
        # Define custom colors
        meic_purple = colors.Color(151/255, 65/255, 146/255)
        meic_lavender = colors.Color(225/255, 164/255, 228/255)
        
        # Add title with date and time
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=meic_purple,
            spaceAfter=10
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.grey,
            spaceAfter=30
        )
        
        # Add section heading style
        section_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=meic_purple,
            spaceAfter=12
        )
        
        story.append(Paragraph("Chat Conversation and Feedback", title_style))
        story.append(Paragraph(f"Generated on: {current_datetime}", subtitle_style))
        
        # Add conversation summary
        story.append(Paragraph("Conversation Summary:", section_style))
        story.append(Paragraph(feedback.get('conversation_summary', ''), styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add persona details
        story.append(Paragraph("About Young Person:", section_style))
        persona = feedback.get('persona', {})
        if persona:
            persona_details = [
                f"Age: {persona.get('age', '')}",
                f"Gender: {persona.get('gender', {}).get('identity', '')}",
                f"Location: {persona.get('location', '')}",
                f"Education: {persona.get('education', {}).get('details', '')}",
                f"Welsh Background: {persona.get('welsh_family', '')}, attends a {persona.get('welsh_school', '')}, interested in {persona.get('welsh_interest', '')}",
                f"Issue: {persona.get('issue', '')}",
                f"Desired Outcome: {persona.get('outcome', '')}"
            ]
            for detail in persona_details:
                story.append(Paragraph(detail, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add conversation
        story.append(Paragraph("Conversation:", section_style))
        story.append(Spacer(1, 12))
        
        # Create conversation table with wrapped text
        conv_data = [['Role', 'Message']]
        for msg in conversation:
            # Convert message content to Paragraph for word wrapping
            wrapped_content = Paragraph(msg['content'], styles['Normal'])
            conv_data.append([msg['role'], wrapped_content])
        
        conv_table = Table(conv_data, colWidths=[1.5*inch, 4.5*inch])
        conv_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), meic_lavender),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(conv_table)
        story.append(Spacer(1, 20))
        
        # Add feedback
        story.append(Paragraph("Feedback:", section_style))
        story.append(Spacer(1, 12))
        
        # Create feedback table with wrapped text
        feedback_data = [
            ['Category', 'Score', 'Feedback'],
            ['Tone of Voice', feedback['tone']['score'], Paragraph(feedback['tone']['feedback'], styles['Normal'])],
            ['Engagement', feedback['engagement']['score'], Paragraph(feedback['engagement']['feedback'], styles['Normal'])],
            ['Resolution', feedback['resolution']['score'], Paragraph(feedback['resolution']['feedback'], styles['Normal'])],
            ['Information Provided', feedback['information']['score'], Paragraph(feedback['information']['feedback'], styles['Normal'])],
            ['Overall', feedback['overall']['score'], Paragraph(feedback['overall']['feedback'], styles['Normal'])]
        ]
        
        feedback_table = Table(feedback_data, colWidths=[2*inch, 1*inch, 3*inch])
        feedback_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), meic_lavender),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))
        story.append(feedback_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error in create_pdf: {str(e)}")
        raise

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
        
        # Generate filename with date and time
        current_datetime = datetime.now().strftime("%d-%m-%Y_%H-%M")
        filename = f"Meic-Training-Chat-{current_datetime}.pdf"
        
        # Return PDF as download
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Server will be available at http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True) 