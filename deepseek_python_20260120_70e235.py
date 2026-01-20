"""
Aipin - DeepSeek जैसी AI वेबसाइट
पूरा कोड एक ही फाइल में
"""

import os
import json
import uuid
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import sqlite3
from functools import wraps
import requests

# लॉगिंग सेटअप
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask ऐप बनाएं
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# कॉन्फ़िगरेशन
app.config['SECRET_KEY'] = 'aipin_secret_key_' + str(uuid.uuid4())
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'aipin.db'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['ALLOWED_EXTENSIONS'] = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 
    'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'mp3', 'mp4', 'wav'
}

# फोल्डर बनाएं
for folder in ['static', 'templates', 'uploads', 'data']:
    os.makedirs(folder, exist_ok=True)

class AipinAI:
    """AI मॉडल क्लास"""
    
    def __init__(self):
        self.knowledge_base = self.load_knowledge_base()
        self.search_engine_enabled = True
        self.model_name = "Aipin-DeepMind"
        
    def load_knowledge_base(self):
        """ज्ञान आधार लोड करें"""
        knowledge_file = 'data/knowledge_base.json'
        if os.path.exists(knowledge_file):
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "general": {
                "नमस्ते": "नमस्ते! मैं Aipin AI हूं। आपकी कैसे मदद कर सकता हूं?",
                "धन्यवाद": "आपका स्वागत है! कोई और प्रश्न?",
                "अलविदा": "अलविदा! फिर मिलेंगे।"
            },
            "programming": {
                "python": "Python एक हाई-लेवल प्रोग्रामिंग भाषा है।\n\nउदाहरण:\n```python\nprint('नमस्ते दुनिया!')\nname = input('आपका नाम: ')\nprint(f'नमस्ते {name}')\n```",
                "javascript": "JavaScript वेब डेवलपमेंट की भाषा है।\n\nउदाहरण:\n```javascript\nconsole.log('Hello World');\nfunction greet(name) {\n  return `Hello ${name}`;\n}\n```",
                "html": "HTML वेब पेज की स्ट्रक्चर बनाता है।\n\nउदाहरण:\n```html\n<!DOCTYPE html>\n<html>\n<head>\n  <title>मेरा पेज</title>\n</head>\n<body>\n  <h1>नमस्ते दुनिया!</h1>\n</body>\n</html>\n```"
            },
            "education": {
                "गणित": "गणित संख्याओं, संरचनाओं, स्थान और परिवर्तन का अध्ययन है।",
                "विज्ञान": "विज्ञान प्रकृति और भौतिक दुनिया का व्यवस्थित अध्ययन है।",
                "इतिहास": "इतिहास मानव अतीत का अध्ययन है।"
            }
        }
    
    def web_search(self, query):
        """वेब खोज करें"""
        try:
            # DuckDuckGo Instant Answer API
            url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=1"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                result = ""
                if data.get('Abstract'):
                    result += f"**सारांश:** {data['Abstract']}\n\n"
                if data.get('AbstractURL'):
                    result += f"**स्रोत:** {data['AbstractURL']}\n\n"
                if data.get('RelatedTopics'):
                    topics = data['RelatedTopics'][:3]
                    result += "**संबंधित विषय:**\n"
                    for topic in topics:
                        if isinstance(topic, dict) and topic.get('Text'):
                            result += f"- {topic['Text'][:100]}...\n"
                return result if result else "वेब खोज से कोई परिणाम नहीं मिला।"
        except:
            pass
        return "वेब खोज अस्थायी रूप से अनुपलब्ध है।"
    
    def generate_response(self, query, use_web_search=False):
        """प्रश्न का उत्तर जनरेट करें"""
        query_lower = query.lower()
        
        # विशेष प्रश्नों के लिए
        special_responses = {
            "तुम्हारा नाम क्या है": "मेरा नाम Aipin है! मैं एक AI असिस्टन्ट हूं।",
            "तुम क्या कर सकते हो": """मैं ये काम कर सकता हूं:
1. प्रश्नों के उत्तर देना
2. कोड लिखने में मदद करना
3. फाइलें प्रोसेस करना
4. वेब से जानकारी खोजना
5. विभिन्न भाषाओं में बातचीत करना""",
            "तुम कैसे हो": "मैं ठीक हूं, धन्यवाद! आप कैसे हैं?",
            "समय बताओ": f"वर्तमान समय: {datetime.now().strftime('%H:%M:%S')}",
            "तारीख बताओ": f"आज की तारीख: {datetime.now().strftime('%d/%m/%Y')}"
        }
        
        for key, response in special_responses.items():
            if key in query_lower:
                return response
        
        # ज्ञान आधार में खोजें
        for category, topics in self.knowledge_base.items():
            for topic, response in topics.items():
                if topic in query_lower:
                    return response
        
        # वेब खोज
        if use_web_search and self.search_engine_enabled:
            web_result = self.web_search(query)
            if web_result:
                return f"वेब खोज परिणाम:\n\n{web_result}\n\n---\n*Aipin AI द्वारा प्रदान किया गया*"
        
        # डिफ़ॉल्ट उत्तर
        default_responses = [
            f"मैं Aipin AI हूं। आपने पूछा: '{query}'\n\nयह एक रोचक प्रश्न है! मैं इसके बारे में और जानकारी प्राप्त कर रहा हूं।",
            f"प्रश्न: '{query}'\n\nमैं इस विषय में विशेषज्ञ नहीं हूं, लेकिन आप इन स्रोतों से जानकारी प्राप्त कर सकते हैं:\n1. विकिपीडिया\n2. कोर्सेरा\n3. खान एकेडमी",
            f"'{query}' के बारे में:\n\nमेरे पास इस समय सटीक जानकारी नहीं है। क्या आप कोई अन्य प्रश्न पूछना चाहेंगे?",
            f"Aipin AI उत्तर: मैं '{query}' के बारे में अभी सीख रहा हूं। कृपया थोड़ी देर बाद पूछें।"
        ]
        
        import random
        return random.choice(default_responses)

class Database:
    """डेटाबेस क्लास"""
    
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """डेटाबेस इनिशियलाइज़ करें"""
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # यूजर्स टेबल
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # चैट हिस्ट्री टेबल
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                query TEXT,
                response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # फाइल्स टेबल
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT,
                filepath TEXT,
                filetype TEXT,
                size INTEGER,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_chat(self, user_id, query, response):
        """चैट सेव करें"""
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO chat_history (user_id, query, response) VALUES (?, ?, ?)',
            (user_id, query, response)
        )
        conn.commit()
        conn.close()
    
    def get_chat_history(self, user_id, limit=50):
        """चैट हिस्ट्री प्राप्त करें"""
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        cursor.execute(
            'SELECT query, response, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
            (user_id, limit)
        )
        history = cursor.fetchall()
        conn.close()
        return history

# AI इंस्टेंस बनाएं
ai_engine = AipinAI()
db = Database()

# हेल्पर फंक्शंस
def allowed_file(filename):
    """फाइल एक्सटेंशन चेक करें"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def analyze_file(filepath):
    """फाइल का विश्लेषण करें"""
    try:
        filename = os.path.basename(filepath)
        ext = filename.split('.')[-1].lower()
        size = os.path.getsize(filepath)
        
        analysis = {
            'filename': filename,
            'extension': ext,
            'size': f"{size:,} bytes",
            'content_type': 'Unknown'
        }
        
        # टेक्स्ट फाइल पढ़ें
        if ext in ['txt', 'py', 'js', 'html', 'css', 'json']:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # पहले 1000 characters
                analysis['preview'] = content[:200] + '...' if len(content) > 200 else content
                analysis['content_type'] = 'Text'
        
        return analysis
    except Exception as e:
        return {'error': str(e)}

# रूट्स
@app.route('/')
def home():
    """होमपेज"""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """स्टेटिक फाइल्स"""
    return send_from_directory('static', filename)

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI चैट एंडपॉइंट"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        use_web_search = data.get('web_search', False)
        user_id = data.get('user_id', 1)  # डिफ़ॉल्ट user_id
        
        if not query:
            return jsonify({'error': 'क्वेरी आवश्यक है'}), 400
        
        # AI से उत्तर प्राप्त करें
        response = ai_engine.generate_response(query, use_web_search)
        
        # डेटाबेस में सेव करें
        db.save_chat(user_id, query, response)
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """फाइल अपलोड"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'कोई फाइल नहीं'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'फाइल का नाम नहीं'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # फाइल विश्लेषण
            analysis = analyze_file(filepath)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'analysis': analysis,
                'message': f'फाइल {filename} अपलोड हो गई'
            })
        
        return jsonify({'error': 'अमान्य फाइल फॉर्मेट'}), 400
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search():
    """वेब सर्च"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'खोज क्वेरी आवश्यक है'}), 400
        
        # वेब खोज करें
        result = ai_engine.web_search(query)
        
        return jsonify({
            'success': True,
            'query': query,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """चैट हिस्ट्री प्राप्त करें"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        history = db.get_chat_history(user_id, limit)
        
        formatted_history = []
        for query, response, timestamp in history:
            formatted_history.append({
                'query': query,
                'response': response,
                'timestamp': timestamp
            })
        
        return jsonify({
            'success': True,
            'history': formatted_history
        })
    
    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/info', methods=['GET'])
def get_info():
    """सिस्टम जानकारी"""
    return jsonify({
        'name': 'Aipin AI',
        'version': '1.0.0',
        'description': 'DeepSeek जैसा AI असिस्टेंट',
        'features': [
            'AI चैट',
            'फाइल अपलोड',
            'वेब खोज',
            'चैट हिस्ट्री',
            'मल्टीलैंग्वेज सपोर्ट'
        ],
        'status': 'active',
        'timestamp': datetime.now().isoformat()
    })

# HTML टेम्पलेट्स
@app.route('/templates/<template_name>')
def serve_template(template_name):
    """टेम्पलेट फाइल्स सर्व करें"""
    return render_template(template_name)

# एडमिन रूट्स
@app.route('/admin')
def admin_panel():
    """एडमिन पैनल"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aipin Admin</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            .stats { background: #f0f0f0; padding: 20px; border-radius: 10px; }
            .btn { background: #4a90e2; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Aipin Admin Panel</h1>
        <div class="stats">
            <h3>सिस्टम स्टेटस</h3>
            <p>AI Status: <span style="color: green;">✅ Active</span></p>
            <p>Database: <span style="color: green;">✅ Connected</span></p>
            <p>Search Engine: <span style="color: green;">✅ Enabled</span></p>
        </div>
        <button class="btn" onclick="location.href='/'">वेबसाइट पर जाएं</button>
    </body>
    </html>
    """

# 404 हैण्डलर
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'पेज नहीं मिला'}), 404

# 500 हैण्डलर
@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'सर्वर त्रुटि'}), 500

# स्टार्टअप फंक्शन
def create_sample_data():
    """सैंपल डेटा बनाएं"""
    # सैंपल ज्ञान आधार
    sample_data = {
        "aipin_info": {
            "aipin क्या है": "Aipin एक AI असिस्टेंट है जो DeepSeek की तरह काम करता है।",
            "aipin के फीचर्स": "1. AI चैट\n2. फाइल अपलोड\n3. वेब खोज\n4. चैट हिस्ट्री",
            "aipin का उपयोग": "आप Aipin से कोई भी प्रश्न पूछ सकते हैं, फाइलें अपलोड कर सकते हैं और वेब खोज कर सकते हैं।"
        },
        "technology": {
            "ai": "AI (कृत्रिम बुद्धिमत्ता) मशीनों द्वारा बुद्धिमत्ता का प्रदर्शन है।",
            "मशीन लर्निंग": "मशीन लर्निंग AI का एक हिस्सा है जो सिस्टम को डेटा से सीखने देता है।",
            "डीप लर्निंग": "डीप लर्निंग न्यूरल नेटवर्क का उपयोग करके मशीन लर्निंग का एक प्रकार है।"
        }
    }
    
    # ज्ञान आधार फाइल में सेव करें
    knowledge_file = 'data/knowledge_base.json'
    existing_data = ai_engine.knowledge_base
    existing_data.update(sample_data)
    
    with open(knowledge_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    print("✅ सैंपल डेटा बनाया गया")

if __name__ == '__main__':
    print("🚀 Aipin AI सर्वर शुरू हो रहा है...")
    print(f"📁 Static folder: {app.static_folder}")
    print(f"📁 Templates folder: {app.template_folder}")
    print(f"💾 Database: {app.config['DATABASE']}")
    
    # सैंपल डेटा बनाएं
    create_sample_data()
    
    # स्टेटिक और टेम्पलेट फाइल्स बनाएं
    create_static_files()
    create_template_files()
    
    print("\n🌐 सर्वर चल रहा है: http://localhost:5000")
    print("⚡ एडमिन पैनल: http://localhost:5000/admin")
    print("\n📞 एंडपॉइंट्स:")
    print("  - GET  /              → होमपेज")
    print("  - POST /api/chat      → AI चैट")
    print("  - POST /api/upload    → फाइल अपलोड")
    print("  - POST /api/search    → वेब खोज")
    print("  - GET  /api/history   → चैट हिस्ट्री")
    print("  - GET  /api/info      → सिस्टम जानकारी")
    print("\n🛑 सर्वर बंद करने के लिए Ctrl+C दबाएं")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

def create_static_files():
    """स्टेटिक फाइल्स बनाएं"""
    # CSS फाइल
    css_content = """
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    body {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #e2e8f0;
        min-height: 100vh;
    }

    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }

    .header {
        text-align: center;
        padding: 40px 20px;
        background: rgba(30, 41, 59, 0.8);
        border-radius: 20px;
        margin-bottom: 30px;
        border: 1px solid #334155;
    }

    .logo {
        font-size: 48px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
    }

    .logo i {
        color: #3b82f6;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }

    .logo-text {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        font-weight: bold;
    }

    .tagline {
        color: #94a3b8;
        font-size: 18px;
        margin-top: 10px;
    }

    .chat-container {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 20px;
        padding: 30px;
        border: 1px solid #334155;
        margin-bottom: 30px;
    }

    .chat-messages {
        height: 500px;
        overflow-y: auto;
        padding: 20px;
        background: rgba(15, 23, 42, 0.6);
        border-radius: 15px;
        margin-bottom: 20px;
    }

    .message {
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 15px;
        max-width: 80%;
        animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .user-message {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 5px;
    }

    .ai-message {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #475569;
        border-bottom-left-radius: 5px;
    }

    .message-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
        font-weight: 600;
    }

    .message-content {
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    .input-area {
        display: flex;
        gap: 15px;
        align-items: flex-end;
    }

    .input-container {
        flex: 1;
        position: relative;
    }

    textarea {
        width: 100%;
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #475569;
        border-radius: 15px;
        color: #e2e8f0;
        padding: 20px;
        font-size: 16px;
        resize: none;
        min-height: 60px;
        max-height: 150px;
        outline: none;
        transition: all 0.3s;
    }

    textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
    }

    .controls {
        display: flex;
        gap: 10px;
        flex-direction: column;
    }

    .btn {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 10px;
        cursor: pointer;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4);
    }

    .btn-secondary {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid #475569;
    }

    .btn-secondary:hover {
        background: rgba(255, 255, 255, 0.15);
    }

    .features {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-top: 40px;
    }

    .feature-card {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 15px;
        padding: 25px;
        border: 1px solid #334155;
        transition: all 0.3s;
    }

    .feature-card:hover {
        transform: translateY(-5px);
        border-color: #3b82f6;
    }

    .feature-icon {
        font-size: 40px;
        color: #3b82f6;
        margin-bottom: 15px;
    }

    .feature-title {
        font-size: 20px;
        margin-bottom: 10px;
        color: #f1f5f9;
    }

    .feature-desc {
        color: #94a3b8;
        line-height: 1.6;
    }

    .file-list {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 15px;
    }

    .file-item {
        background: rgba(59, 130, 246, 0.2);
        padding: 8px 15px;
        border-radius: 8px;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .loading {
        text-align: center;
        padding: 20px;
    }

    .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid rgba(59, 130, 246, 0.3);
        border-top: 3px solid #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 15px;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .quick-actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 20px;
    }

    .quick-btn {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #475569;
        color: #e2e8f0;
        padding: 10px 20px;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s;
    }

    .quick-btn:hover {
        background: rgba(59, 130, 246, 0.2);
        border-color: #3b82f6;
    }

    .footer {
        text-align: center;
        padding: 30px;
        color: #94a3b8;
        font-size: 14px;
        border-top: 1px solid #334155;
        margin-top: 50px;
    }

    .code-block {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        overflow-x: auto;
        border-left: 4px solid #3b82f6;
    }

    .code-block pre {
        margin: 0;
        font-family: 'Courier New', monospace;
        font-size: 14px;
    }

    .stats {
        display: flex;
        gap: 20px;
        justify-content: center;
        margin-top: 20px;
    }

    .stat-item {
        background: rgba(30, 41, 59, 0.8);
        padding: 15px 25px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #334155;
    }

    .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #3b82f6;
    }

    .stat-label {
        font-size: 14px;
        color: #94a3b8;
        margin-top: 5px;
    }

    @media (max-width: 768px) {
        .container {
            padding: 15px;
        }
        
        .features {
            grid-template-columns: 1fr;
        }
        
        .input-area {
            flex-direction: column;
        }
        
        .controls {
            flex-direction: row;
            width: 100%;
            justify-content: center;
        }
        
        .btn {
            flex: 1;
            justify-content: center;
        }
        
        .chat-messages {
            height: 400px;
        }
    }
    """
    
    # JavaScript फाइल
    js_content = """
    // Aipin AI JavaScript
    class AipinApp {
        constructor() {
            this.apiBase = window.location.origin;
            this.chatMessages = document.getElementById('chatMessages');
            this.messageInput = document.getElementById('messageInput');
            this.sendBtn = document.getElementById('sendBtn');
            this.fileInput = document.getElementById('fileInput');
            this.fileList = document.getElementById('fileList');
            this.webSearchToggle = document.getElementById('webSearchToggle');
            this.clearChatBtn = document.getElementById('clearChatBtn');
            this.loadHistoryBtn = document.getElementById('loadHistoryBtn');
            this.quickActions = document.querySelectorAll('.quick-btn');
            this.webSearchEnabled = false;
            this.chatHistory = [];
            
            this.init();
        }
        
        init() {
            // Event Listeners
            this.sendBtn.addEventListener('click', () => this.sendMessage());
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
            this.webSearchToggle.addEventListener('click', () => this.toggleWebSearch());
            this.clearChatBtn.addEventListener('click', () => this.clearChat());
            this.loadHistoryBtn.addEventListener('click', () => this.loadChatHistory());
            
            // Quick Actions
            this.quickActions.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const question = e.target.dataset.question;
                    this.messageInput.value = question;
                    this.sendMessage();
                });
            });
            
            // Auto-resize textarea
            this.messageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
            
            // Initial message
            this.addMessage('ai', 'नमस्ते! मैं Aipin AI हूं। आपकी कैसे मदद कर सकता हूं?');
        }
        
        async sendMessage() {
            const message = this.messageInput.value.trim();
            if (!message) return;
            
            // Add user message
            this.addMessage('user', message);
            this.messageInput.value = '';
            this.messageInput.style.height = 'auto';
            
            // Show loading
            this.showLoading();
            
            try {
                // Send to API
                const response = await fetch(`${this.apiBase}/api/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: message,
                        web_search: this.webSearchEnabled,
                        user_id: 1
                    })
                });
                
                const data = await response.json();
                
                // Remove loading
                this.hideLoading();
                
                if (data.success) {
                    this.addMessage('ai', data.response);
                    // Save to local history
                    this.chatHistory.push({
                        query: message,
                        response: data.response,
                        timestamp: new Date().toISOString()
                    });
                } else {
                    this.addMessage('ai', `त्रुटि: ${data.error}`);
                }
                
            } catch (error) {
                this.hideLoading();
                this.addMessage('ai', `नेटवर्क त्रुटि: ${error.message}`);
            }
            
            // Scroll to bottom
            this.scrollToBottom();
        }
        
        addMessage(sender, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            
            const header = document.createElement('div');
            header.className = 'message-header';
            
            if (sender === 'user') {
                header.innerHTML = '<i class="fas fa-user"></i> आप';
            } else {
                header.innerHTML = '<i class="fas fa-robot"></i> Aipin AI';
            }
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            // Format code blocks
            let formattedContent = content;
            const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
            formattedContent = formattedContent.replace(codeBlockRegex, (match, lang, code) => {
                return `<div class="code-block"><pre><code>${code.trim()}</code></pre></div>`;
            });
            
            contentDiv.innerHTML = formattedContent;
            
            messageDiv.appendChild(header);
            messageDiv.appendChild(contentDiv);
            
            this.chatMessages.appendChild(messageDiv);
            this.scrollToBottom();
        }
        
        async handleFileUpload(event) {
            const files = event.target.files;
            if (!files.length) return;
            
            // Clear file list
            this.fileList.innerHTML = '';
            
            for (let file of files) {
                // Show in file list
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.innerHTML = `
                    <i class="fas fa-file"></i>
                    <span>${file.name}</span>
                    <small>(${Math.round(file.size / 1024)} KB)</small>
                `;
                this.fileList.appendChild(fileItem);
                
                // Upload to server
                await this.uploadFile(file);
            }
        }
        
        async uploadFile(file) {
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch(`${this.apiBase}/api/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.addMessage('ai', `फाइल "${data.filename}" अपलोड हुई।\nविश्लेषण: ${JSON.stringify(data.analysis, null, 2)}`);
                } else {
                    this.addMessage('ai', `फाइल अपलोड विफल: ${data.error}`);
                }
            } catch (error) {
                this.addMessage('ai', `अपलोड त्रुटि: ${error.message}`);
            }
        }
        
        toggleWebSearch() {
            this.webSearchEnabled = !this.webSearchEnabled;
            const btn = this.webSearchToggle;
            
            if (this.webSearchEnabled) {
                btn.innerHTML = '<i class="fas fa-globe"></i> वेब खोज: ON';
                btn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                this.addMessage('ai', 'वेब खोज सक्षम किया गया है। अब मैं वेब से नवीनतम जानकारी प्राप्त कर सकता हूं।');
            } else {
                btn.innerHTML = '<i class="fas fa-globe"></i> वेब खोज: OFF';
                btn.style.background = '';
                this.addMessage('ai', 'वेब खोज अक्षम किया गया है।');
            }
        }
        
        clearChat() {
            if (confirm('क्या आप चैट हिस्ट्री साफ करना चाहते हैं?')) {
                this.chatMessages.innerHTML = '';
                this.addMessage('ai', 'चैट हिस्ट्री साफ की गई है। नमस्ते! मैं Aipin AI हूं।');
            }
        }
        
        async loadChatHistory() {
            try {
                const response = await fetch(`${this.apiBase}/api/history?user_id=1&limit=10`);
                const data = await response.json();
                
                if (data.success && data.history.length > 0) {
                    // Clear current chat
                    this.chatMessages.innerHTML = '';
                    
                    // Add history messages
                    for (let chat of data.history.reverse()) {
                        this.addMessage('user', chat.query);
                        this.addMessage('ai', chat.response);
                    }
                    
                    this.addMessage('ai', 'चैट हिस्ट्री लोड की गई है। मैं Aipin AI हूं, आपकी कैसे मदद करूं?');
                } else {
                    this.addMessage('ai', 'कोई चैट हिस्ट्री नहीं मिली।');
                }
            } catch (error) {
                this.addMessage('ai', `हिस्ट्री लोड त्रुटि: ${error.message}`);
            }
        }
        
        showLoading() {
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.id = 'loading';
            loadingDiv.innerHTML = `
                <div class="spinner"></div>
                <p>Aipin सोच रहा है...</p>
            `;
            this.chatMessages.appendChild(loadingDiv);
            this.scrollToBottom();
        }
        
        hideLoading() {
            const loading = document.getElementById('loading');
            if (loading) loading.remove();
        }
        
        scrollToBottom() {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
        
        async searchWeb(query) {
            try {
                const response = await fetch(`${this.apiBase}/api/search`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query })
                });
                
                const data = await response.json();
                return data.success ? data.result : `खोज त्रुटि: ${data.error}`;
            } catch (error) {
                return `नेटवर्क त्रुटि: ${error.message}`;
            }
        }
        
        async getSystemInfo() {
            try {
                const response = await fetch(`${this.apiBase}/api/info`);
                const data = await response.json();
                
                let info = `**Aipin AI सिस्टम जानकारी**\\n`;
                info += `Name: ${data.name}\\n`;
                info += `Version: ${data.version}\\n`;
                info += `Status: ${data.status}\\n`;
                info += `\\n**फीचर्स:**\\n`;
                data.features.forEach((feature, i) => {
                    info += `${i+1}. ${feature}\\n`;
                });
                
                this.addMessage('ai', info);
            } catch (error) {
                this.addMessage('ai', `जानकारी प्राप्त करने में त्रुटि: ${error.message}`);
            }
        }
    }
    
    // Initialize app when page loads
    document.addEventListener('DOMContentLoaded', () => {
        window.aipinApp = new AipinApp();
        console.log('Aipin AI App initialized');
    });
    """
    
    # फाइल्स सेव करें
    with open('static/style.css', 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    with open('static/script.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print("✅ स्टेटिक फाइल्स बनाई गईं")

def create_template_files():
    """HTML टेम्पलेट फाइल्स बनाएं"""
    html_content = """
    <!DOCTYPE html>
    <html lang="hi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Aipin AI - DeepSeek जैसा AI असिस्टेंट</title>
        <link rel="stylesheet" href="/static/style.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="icon" type="image/x-icon" href="https://img.icons8.com/color/96/000000/artificial-intelligence.png">
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <div class="logo">
                    <i class="fas fa-brain"></i>
                    <h1 class="logo-text">Aipin AI</h1>
                </div>
                <p class="tagline">DeepSeek जैसा शक्तिशाली AI असिस्टेंट</p>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-value" id="aiStatus">ONLINE</div>
                        <div class="stat-label">AI Status</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="chatCount">0</div>
                        <div class="stat-label">चैट्स</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">हिंदी</div>
                        <div class="stat-label">भाषा</div>
                    </div>
                </div>
            </div>

            <!-- Chat Container -->
            <div class="chat-container">
                <div class="chat-messages" id="chatMessages">
                    <!-- Messages will appear here -->
                </div>
                
                <div class="input-area">
                    <div class="input-container">
                        <textarea 
                            id="messageInput" 
                            placeholder="अपना प्रश्न यहाँ लिखें... (Enter to send, Shift+Enter for new line)"
                            rows="1"
                        ></textarea>
                        
                        <div class="file-list" id="fileList"></div>
                    </div>
                    
                    <div class="controls">
                        <button class="btn" id="sendBtn">
                            <i class="fas fa-paper-plane"></i> भेजें
                        </button>
                        
                        <div class="quick-actions">
                            <button class="quick-btn" data-question="तुम्हारा नाम क्या है">
                                <i class="fas fa-robot"></i> परिचय
                            </button>
                            <button class="quick-btn" data-question="समय बताओ">
                                <i class="fas fa-clock"></i> समय
                            </button>
                            <button class="quick-btn" data-question="Python में Hello World">
                                <i class="fab fa-python"></i> Python
                            </button>
                            <button class="quick-btn" data-question="वेब डेवलपमेंट">
                                <i class="fas fa-code"></i> Coding
                            </button>
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 20px; display: flex; gap: 10px; flex-wrap: wrap;">
                    <button class="btn btn-secondary" id="webSearchToggle">
                        <i class="fas fa-globe"></i> वेब खोज: OFF
                    </button>
                    
                    <button class="btn btn-secondary" id="loadHistoryBtn">
                        <i class="fas fa-history"></i> हिस्ट्री लोड करें
                    </button>
                    
                    <button class="btn btn-secondary" id="clearChatBtn">
                        <i class="fas fa-trash"></i> चैट साफ करें
                    </button>
                    
                    <label class="btn btn-secondary" style="cursor: pointer;">
                        <i class="fas fa-paperclip"></i> फाइल अपलोड
                        <input type="file" id="fileInput" multiple style="display: none;">
                    </label>
                </div>
            </div>

            <!-- Features -->
            <div class="features">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-comments"></i>
                    </div>
                    <h3 class="feature-title">AI चैट</h3>
                    <p class="feature-desc">
                        प्राकृतिक भाषा में बातचीत करें। हिंदी और अंग्रेजी दोनों में प्रश्न पूछें।
                    </p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-search"></i>
                    </div>
                    <h3 class="feature-title">वेब खोज</h3>
                    <p class="feature-desc">
                        रियल-टाइम वेब सर्च के साथ नवीनतम जानकारी प्राप्त करें।
                    </p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-file-upload"></i>
                    </div>
                    <h3 class="feature-title">फाइल अपलोड</h3>
                    <p class="feature-desc">
                        PDF, Images, Documents अपलोड करें और उनका विश्लेषण करें।
                    </p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-history"></i>
                    </div>
                    <h3 class="feature-title">चैट हिस्ट्री</h3>
                    <p class="feature-desc">
                        सभी चैट सेव रहती हैं। कभी भी पिछली बातचीत देख सकते हैं।
                    </p>
                </div>
            </div>

            <!-- Footer -->
            <div class="footer">
                <p>© 2024 Aipin AI - Made in India 🇮🇳</p>
                <p style="margin-top: 10px; font-size: 12px;">
                    <i class="fas fa-info-circle"></i> 
                    Aipin AI एक डेमो प्रोजेक्ट है। असली AI मॉडल integrate करने के लिए OpenAI या अन्य API का उपयोग करें।
                </p>
                <div style="margin-top: 15px;">
                    <a href="/admin" style="color: #94a3b8; text-decoration: none; margin: 0 10px;">
                        <i class="fas fa-cog"></i> एडमिन
                    </a>
                    <a href="/api/info" style="color: #94a3b8; text-decoration: none; margin: 0 10px;">
                        <i class="fas fa-info"></i> API जानकारी
                    </a>
                    <a href="https://github.com" style="color: #94a3b8; text-decoration: none; margin: 0 10px;">
                        <i class="fab fa-github"></i> GitHub
                    </a>
                </div>
            </div>
        </div>

        <script src="/static/script.js"></script>
        <script>
            // Chat counter
            let chatCount = 0;
            document.getElementById('sendBtn').addEventListener('click', () => {
                chatCount++;
                document.getElementById('chatCount').textContent = chatCount;
            });
            
            // Auto-focus on input
            document.getElementById('messageInput').focus();
            
            // System status check
            fetch('/api/info')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'active') {
                        document.getElementById('aiStatus').style.color = '#10b981';
                    }
                })
                .catch(() => {
                    document.getElementById('aiStatus').textContent = 'OFFLINE';
                    document.getElementById('aiStatus').style.color = '#ef4444';
                });
        </script>
    </body>
    </html>
    """
    
    # HTML फाइल सेव करें
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ HTML टेम्पलेट बनाई गई")

# रन करने के लिए
if __name__ == '__main__':
    # अगर सीधे रन कर रहे हैं
    create_sample_data()
    create_static_files()
    create_template_files()
    
    print("\n" + "="*50)
    print("🎯 Aipin AI वेबसाइट तैयार है!")
    print("="*50)
    print("\n🚀 सर्वर शुरू करने के लिए:")
    print("1. इस फाइल को सेव करें: aipin_complete.py")
    print("2. टर्मिनल में चलाएं: python aipin_complete.py")
    print("3. ब्राउज़र में खोलें: http://localhost:5000")
    print("\n📦 आवश्यक पैकेजेस:")
    print("   pip install flask flask-cors requests")
    print("\n⚡ फीचर्स:")
    print("   - AI चैट (हिंदी/English)")
    print("   - वेब खोज")
    print("   - फाइल अपलोड")
    print("   - चैट हिस्ट्री")
    print("   - डेटाबेस स्टोरेज")
    print("\n🔥 त्वरित शुरुआत:")
    print("   python aipin_complete.py")