import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Sidebar Background (Differentiate Menu Bar)
# Currently: background-color: #0A0A0B !important; border-right: 1px solid #222 !important;
content = re.sub(
    r'\[data-testid="stSidebar"\] \{\s*background-color: #[0-9A-Fa-f]+ !important;\s*border-right: 1px solid #[0-9A-Fa-f]+ !important;',
    r'[data-testid="stSidebar"] {\n        background-color: #0B0F19 !important;\n        border-right: 1px solid #1E293B !important;',
    content
)

# 2. Update Clean Cards (Differentiate Content Descriptions/Main Area)
# Currently: background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08);
content = re.sub(
    r'\.clean-card \{\s*background: rgba\(255, 255, 255, 0\.03\);',
    r'.clean-card {\n        background: #0F172A;',
    content
)

# 3. Update Chat Input Box (Differentiate Chat)
# Currently: background-color: #0A0A0B !important; border: 1px solid #333333 !important;
content = re.sub(
    r'div\[data-testid="stChatInput"\] \{\s*background-color: #0A0A0B !important;\s*border: 1px solid #333333 !important;',
    r'div[data-testid="stChatInput"] {\n        background-color: #1E293B !important;\n        border: 1px solid #334155 !important;',
    content
)
content = re.sub(
    r'div\[data-testid="stChatInput"\] textarea \{\s*background-color: #0A0A0B !important;',
    r'div[data-testid="stChatInput"] textarea {\n        background-color: #1E293B !important;',
    content
)

# 4. Update the "Speech-to-Text" Mic input box to match Chat Input shade
# Currently: background-color: #0A0A0B; border: 1px solid #333;
content = content.replace(
    'background-color: #0A0A0B; border: 1px solid #333; padding: 16px; border-radius: 8px;',
    'background-color: #1E293B; border: 1px solid #334155; padding: 16px; border-radius: 8px;'
)

# 5. Fix the text input inside the Speech box to have a slightly darker inlay
# Currently: background: #111; border: 1px solid #EAEAEA;
content = content.replace(
    'border: 1px solid #EAEAEA; background: #111;',
    'border: 1px solid #334155; background: #0F172A;'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Color shades updated!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Primary Color (60% Black) -> #0A0A0B
# Secondary Color (30% Deep Grey) -> #1F1F1F
# Accent Color (10% Blue) -> #38BDF8

# 1. Main Backgrounds (60%)
content = re.sub(
    r'background-color: #[0-9A-Fa-f]+ !important;\s*color: #E2E8F0;',
    r'background-color: #0A0A0B !important;\n        color: #E2E8F0;',
    content
)

# 2. Sidebar (60%)
content = re.sub(
    r'\[data-testid="stSidebar"\] \{\s*background-color: #[0-9A-Fa-f]+ !important;\s*border-right: 1px solid #[0-9A-Fa-f]+ !important;',
    r'[data-testid="stSidebar"] {\n        background-color: #0A0A0B !important;\n        border-right: 1px solid #1F1F1F !important;',
    content
)

# 3. Clean Cards (30%)
content = re.sub(
    r'\.clean-card \{\s*background: #[0-9A-Fa-f]+;',
    r'.clean-card {\n        background: #1F1F1F;',
    content
)
# Re-catch the earlier clean-card hover state border color to use accent or grey
content = content.replace('border-color: rgba(255, 255, 255, 0.2);', 'border-color: #38BDF8;')

# 4. Chat Input / Mic Box (30%)
content = re.sub(
    r'div\[data-testid="stChatInput"\] \{\s*background-color: #[0-9A-Fa-f]+ !important;\s*border: 1px solid #[0-9A-Fa-f]+ !important;',
    r'div[data-testid="stChatInput"] {\n        background-color: #1F1F1F !important;\n        border: 1px solid #333333 !important;',
    content
)
content = re.sub(
    r'div\[data-testid="stChatInput"\] textarea \{\s*background-color: #[0-9A-Fa-f]+ !important;',
    r'div[data-testid="stChatInput"] textarea {\n        background-color: #1F1F1F !important;',
    content
)

# Speech-to-Text Div background
content = content.replace('background-color: #1E293B; border: 1px solid #334155; padding: 16px; border-radius: 8px;', 'background-color: #1F1F1F; border: 1px solid #333333; padding: 16px; border-radius: 8px;')
content = content.replace('background-color: #0A0A0B; border: 1px solid #333; padding: 16px; border-radius: 8px;', 'background-color: #1F1F1F; border: 1px solid #333333; padding: 16px; border-radius: 8px;')

# Inner transcription box
content = content.replace('border: 1px solid #334155; background: #0F172A;', 'border: 1px solid #333333; background: #0A0A0B;')
content = content.replace('border: 1px solid #EAEAEA; background: #111;', 'border: 1px solid #333333; background: #0A0A0B;')

# Generic baseweb inputs (30%)
content = re.sub(
    r'div\[data-baseweb="input"\] \{\s*background-color: #[0-9A-Fa-f]+ !important;\s*border-color: #[0-9A-Fa-f]+ !important;',
    r'div[data-baseweb="input"] {\n        background-color: #1F1F1F !important;\n        border-color: #333333 !important;',
    content
)

# Selectbox (30%)
content = content.replace('background-color: #1A1A1C;', 'background-color: #1F1F1F;')

# Role Access Scopes (badges) -> Make them 30% background
content = content.replace("background-color: #111111; color: #38BDF8; font-family", "background-color: #1F1F1F; color: #38BDF8; font-family")

# Expander Content Background
content = content.replace('background-color: #0A0A0B !important;', 'background-color: #1F1F1F !important;')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

# Update config.toml
config_path = ".streamlit/config.toml"
try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = f.read()
    config = config.replace('backgroundColor="#050505"', 'backgroundColor="#0A0A0B"')
    config = config.replace('secondaryBackgroundColor="#0A0A0B"', 'secondaryBackgroundColor="#1F1F1F"')
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config)
except Exception:
    pass

print("60-30-10 palette applied!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Global Font to Work Sans
content = content.replace(
    "html, body, [class*=\"css\"], .stApp {\n        font-family: 'JetBrains Mono', monospace !important;",
    "html, body, [class*=\"css\"], .stApp {\n        font-family: 'Work Sans', sans-serif !important;"
)

# 2. Explicitly ensure code tags still get JetBrains Mono
code_font_css = """
    code, pre, .stCodeBlock {
        font-family: 'JetBrains Mono', monospace !important;
    }
"""
content = content.replace("</style>", code_font_css + "\n</style>")

# 3. Fix the Audit Log explicitly (since it has inline style)
content = content.replace(
    "font-family:'JetBrains Mono', monospace;",
    "font-family:'Work Sans', sans-serif;"
)
# Ensure the secondary border in audit logs matches the 30% palette (#333333 instead of #EAEAEA)
content = content.replace("border-bottom: 1px solid #EAEAEA;", "border-bottom: 1px solid #333333;")

# 4. Make sure list items inherit DM Sans if they are generic descriptions, or let them fall back to Work Sans.
# Let's add li to the DM Sans block so bullet points in the sidebar match the paragraph descriptions.
content = content.replace(
    "p, .stMarkdown p {",
    "p, .stMarkdown p, li, .stMarkdown li {"
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

# Update config.toml
config_path = ".streamlit/config.toml"
try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = f.read()
    config = config.replace('font="monospace"', 'font="sans serif"')
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config)
except Exception:
    pass

print("Font fixes applied!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Font Import to include Work Sans
content = re.sub(
    r"@import url\('https://fonts.googleapis.com/css2[^']+'\);",
    "@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=Work+Sans:wght@300;400;500;600;700&display=swap');",
    content
)

# 2. Update widget labels (ACTIVE PERSONA SWITCHER)
content = re.sub(
    r"div\[data-testid=\"stSelectbox\"\] label,\s*div\[data-testid=\"stWidgetLabel\"\] p,\s*label p \{\s*font-family: 'JetBrains Mono', monospace !important;",
    "div[data-testid=\"stSelectbox\"] label, div[data-testid=\"stWidgetLabel\"] p, label p { font-family: 'Work Sans', sans-serif !important;",
    content
)

# 3. Update Chat Input & textareas (Enter your operations query...)
content = re.sub(
    r"div\[data-testid=\"stChatInput\"\] textarea \{\s*background-color: #1F1F1F !important;\s*color: #E2E8F0 !important;\s*font-family: 'JetBrains Mono', monospace !important;",
    "div[data-testid=\"stChatInput\"] textarea { background-color: #1F1F1F !important; color: #E2E8F0 !important; font-family: 'Work Sans', sans-serif !important;",
    content
)
content = re.sub(
    r"div\[data-baseweb=\"input\"\] input, div\[data-baseweb=\"textarea\"\] textarea \{\s*color: #E2E8F0 !important;\s*font-family: 'JetBrains Mono', monospace !important;",
    "div[data-baseweb=\"input\"] input, div[data-baseweb=\"textarea\"] textarea { color: #E2E8F0 !important; font-family: 'Work Sans', sans-serif !important;",
    content
)

# 4. Update the Persona Banner (Logged in as Ravi...)
# The persona banner uses global font if not set. Let's explicitly set it in CSS.
if ".persona-banner {" in content:
    content = content.replace(
        ".persona-banner {\n        background-color: rgba(255, 255, 255, 0.03);",
        ".persona-banner {\n        font-family: 'Work Sans', sans-serif !important;\n        background-color: rgba(255, 255, 255, 0.03);"
    )
# Let's ensure it has the rule using regex
content = re.sub(
    r'\.persona-banner \{\s*',
    r'.persona-banner {\n        font-family: \'Work Sans\', sans-serif !important;\n        ',
    content
)

# 5. Update the Role Access Scope inline badges
content = content.replace(
    "font-family: \\\"JetBrains Mono\\\", monospace;",
    "font-family: \\\"Work Sans\\\", sans-serif;"
)

# Let's make sure the inline transcription box in Speech-to-Text uses Work Sans too
content = content.replace(
    "font-family: 'JetBrains Mono', monospace;\" readonly>",
    "font-family: 'Work Sans', sans-serif;\" readonly>"
)

# Let's make sure the speech status ("Click to speak...") uses Work Sans too (optional, but it's an input-like thing)
content = content.replace(
    "font-family: 'JetBrains Mono', monospace; font-weight: 500; text-transform: uppercase;",
    "font-family: 'Work Sans', sans-serif; font-weight: 500; text-transform: uppercase;"
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Work Sans applied to circled elements!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

chat_input_css = """
    /* Dark Theme for Chat Input / Query Box */
    div[data-testid="stChatInput"] {
        background-color: #0A0A0B !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: #0A0A0B !important;
        color: #E2E8F0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        -webkit-text-fill-color: #E2E8F0 !important;
    }
    div[data-testid="stChatInput"] button {
        background-color: transparent !important;
        color: #38BDF8 !important;
    }
    div[data-testid="stChatInput"] button svg {
        fill: #38BDF8 !important;
    }
    /* General text input boxes */
    div[data-baseweb="input"] {
        background-color: #0A0A0B !important;
        border-color: #333 !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
        color: #E2E8F0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        -webkit-text-fill-color: #E2E8F0 !important;
    }
"""

content = content.replace("</style>", chat_input_css + "\n</style>")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Chat input CSS appended!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = [
    # General descriptive grey text
    (r"color: #888;", r"color: #94A3B8;"),
    (r"color:#6b7280;", r"color:#94A3B8;"),
    (r"color: #666666;", r"color: #94A3B8;"),
    (r"color: #4b5563;", r"color: #94A3B8;"),
    (r"color:#4b5563;", r"color:#94A3B8;"),
    (r"color:#888888;", r"color:#94A3B8;"),
    
    # Broken contrast (black text on black background)
    (r"color: #000;", r"color: #E2E8F0;"),
    (r'status_color = "#111111"', r'status_color = "#10B981"'), # Success color (green)
    (r'else "#666666"', r'else "#EF4444"'), # Error color (red)
    
    # Fix the borders
    (r"border-left: 4px solid #666666;", r"border-left: 4px solid #10B981;"),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Contrast fixes applied!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the bright white button CSS with a sleek terminal-style blue button CSS
old_button_css = """    div.stButton > button {
        background-color: #FFFFFF;
        color: #E2E8F0;
        border: 1px solid #FFFFFF;
        border-radius: 2px;
        padding: 8px 24px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: transparent;
        color: #FFFFFF;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
    }"""

new_button_css = """    div.stButton > button {
        background-color: rgba(56, 189, 248, 0.05) !important;
        color: #38BDF8 !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 4px !important;
        padding: 8px 24px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        background-color: rgba(56, 189, 248, 0.15) !important;
        border-color: #38BDF8 !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.3) !important;
    }"""

# Sometimes the color was left as #000 depending on previous replacements, use regex
content = re.sub(r'div\.stButton > button \{[\s\S]*?\}', new_button_css.split("}")[0] + "}", content)
content = re.sub(r'div\.stButton > button:hover \{[\s\S]*?\}', new_button_css.split("}")[1] + "}", content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated global button styling!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Append specific label styling to the CSS block
label_style = """
    /* Override Streamlit Label Styling */
    div[data-testid="stSelectbox"] label, 
    div[data-testid="stWidgetLabel"] p,
    label p {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.85em !important;
    }
    
    strong, b {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        color: #E2E8F0 !important;
    }
"""

# Insert right before </style>
content = content.replace("</style>", label_style + "</style>")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Label styling fixed!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the recognition JS logic to support toggle and "RECORDED" state
old_js = """        let recognition;
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            recognition.onstart = () => {
                micBtn.style.background = 'rgba(239, 68, 68, 0.1)';
                micBtn.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                micBtn.style.boxShadow = '0 0 15px rgba(239, 68, 68, 0.4)';
                micSvg.setAttribute('stroke', '#EF4444');
                micStatus.innerHTML = '<span style="display:inline-block; width:6px; height:6px; background-color:#EF4444; border-radius:50%; box-shadow: 0 0 8px #EF4444; animation: pulse 1s infinite;"></span> <span style="color: #EF4444;">Listening...</span>';
            };
            
            recognition.onend = () => {
                micBtn.style.background = 'rgba(56, 189, 248, 0.1)';
                micBtn.style.borderColor = 'rgba(56, 189, 248, 0.4)';
                micBtn.style.boxShadow = '0 0 10px rgba(56, 189, 248, 0.1)';
                micSvg.setAttribute('stroke', '#38BDF8');
                micStatus.innerHTML = '<span style="display:inline-block; width:6px; height:6px; background-color:#38BDF8; border-radius:50%; box-shadow: 0 0 8px #38BDF8; animation: pulse 2s infinite;"></span> <span style="color: #38BDF8;">Click to speak...</span>';
            };
            
            recognition.onresult = (event) => {
                const speechToText = event.results[0][0].transcript;
                transBox.value = speechToText;
            };
            
            recognition.onerror = (event) => {
                micStatus.innerText = 'Error: ' + event.error;
            };
        } else {
            micStatus.innerText = 'Speech API not supported.';
            micBtn.disabled = true;
        }
        
        micBtn.addEventListener('click', () => {
            if (recognition) {
                recognition.start();
            }
        });"""

new_js = """        let recognition;
        let isRecording = false;
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            recognition.onstart = () => {
                isRecording = true;
                micBtn.style.background = 'rgba(239, 68, 68, 0.1)';
                micBtn.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                micBtn.style.boxShadow = '0 0 15px rgba(239, 68, 68, 0.4)';
                micSvg.setAttribute('stroke', '#EF4444');
                micStatus.innerHTML = '<span style="display:inline-block; width:6px; height:6px; background-color:#EF4444; border-radius:50%; box-shadow: 0 0 8px #EF4444; animation: pulse 1s infinite;"></span> <span style="color: #EF4444;">Listening...</span>';
            };
            
            recognition.onend = () => {
                isRecording = false;
                micBtn.style.background = 'rgba(16, 185, 129, 0.1)';
                micBtn.style.borderColor = 'rgba(16, 185, 129, 0.4)';
                micBtn.style.boxShadow = '0 0 10px rgba(16, 185, 129, 0.1)';
                micSvg.setAttribute('stroke', '#10B981');
                micStatus.innerHTML = '<span style="display:inline-block; width:6px; height:6px; background-color:#10B981; border-radius:50%; box-shadow: 0 0 8px #10B981;"></span> <span style="color: #10B981;">Recorded!</span>';
                
                // Revert to default blue standby state after 2.5 seconds
                setTimeout(() => {
                    if (!isRecording) {
                        micBtn.style.background = 'rgba(56, 189, 248, 0.1)';
                        micBtn.style.borderColor = 'rgba(56, 189, 248, 0.4)';
                        micBtn.style.boxShadow = '0 0 10px rgba(56, 189, 248, 0.1)';
                        micSvg.setAttribute('stroke', '#38BDF8');
                        micStatus.innerHTML = '<span style="display:inline-block; width:6px; height:6px; background-color:#38BDF8; border-radius:50%; box-shadow: 0 0 8px #38BDF8; animation: pulse 2s infinite;"></span> <span style="color: #38BDF8;">Click to speak...</span>';
                    }
                }, 2500);
            };
            
            recognition.onresult = (event) => {
                const speechToText = event.results[0][0].transcript;
                transBox.value = speechToText;
            };
            
            recognition.onerror = (event) => {
                isRecording = false;
                micStatus.innerText = 'Error: ' + event.error;
            };
        } else {
            micStatus.innerText = 'Speech API not supported.';
            micBtn.disabled = true;
        }
        
        micBtn.addEventListener('click', () => {
            if (recognition) {
                if (!isRecording) {
                    recognition.start();
                } else {
                    recognition.stop();
                }
            }
        });"""

content = content.replace(old_js, new_js)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated recording toggle state!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Hide Header Anchors (Link Popups)
hide_anchors_css = """
    /* Hide Streamlit Header Anchor Links */
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
        display: none !important;
    }
"""
content = content.replace("</style>", hide_anchors_css + "</style>")

# 2. Redefine Mic Button and Text
old_mic_html = """<button id="mic-btn" style="background: transparent; border: 1px solid #FFFFFF; border-radius: 4px; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s;">"""
new_mic_html = """<button id="mic-btn" style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 50%; width: 44px; height: 44px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); box-shadow: 0 0 10px rgba(56, 189, 248, 0.1);" onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 0 15px rgba(56, 189, 248, 0.3)';" onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 0 10px rgba(56, 189, 248, 0.1)';">"""
content = content.replace(old_mic_html, new_mic_html)

# Add hover effect for mic button in CSS
# Instead of inline, I used onmouseover/onmouseout for simplicity in the iframe.

# 3. Change Mic SVG Color to match accent
old_svg = """stroke="#FFFFFF" stroke-width="2\""""
new_svg = """stroke="#38BDF8" stroke-width="2\""""
content = content.replace(old_svg, new_svg)

# 4. Beautify "Click to speak..." text
old_text = """<span id="mic-status" style="font-size: 0.9em; color: #94A3B8;">Click to speak...</span>"""
new_text = """<span id="mic-status" style="font-size: 0.85em; color: #38BDF8; font-family: 'JetBrains Mono', monospace; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 8px;"><span style="display:inline-block; width:6px; height:6px; background-color:#38BDF8; border-radius:50%; box-shadow: 0 0 8px #38BDF8; animation: pulse 2s infinite;"></span> Click to speak...</span>
<style>@keyframes pulse { 0% { opacity: 0.5; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.2); } 100% { opacity: 0.5; transform: scale(0.8); } }</style>"""
content = content.replace(old_text, new_text)

# Also update the transcript box font to match the aesthetic (it was 'Inter')
content = content.replace("font-family: 'Inter', sans-serif;\" readonly>", "font-family: 'JetBrains Mono', monospace;\" readonly>")

# Also fix the copy button font
content = content.replace("font-family: 'Inter', sans-serif; transition", "font-family: 'JetBrains Mono', monospace; text-transform: uppercase; transition")
content = content.replace("background: #FFFFFF; border: 1px solid #FFFFFF; border-radius: 4px; color: #000000; padding: 10px 20px; cursor: pointer; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; transition: all 0.3s;\">Copy</button>", "background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #E2E8F0; padding: 10px 20px; cursor: pointer; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; transition: all 0.3s;\" onmouseover=\"this.style.background='rgba(255,255,255,0.1)';\" onmouseout=\"this.style.background='rgba(255,255,255,0.05)';\">COPY</button>")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("UI polished!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Update the Google Fonts import
old_import = "@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700;800&family=Fira+Code:wght@300;400;500;600;700&display=swap');"
new_import = "@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;700;800&display=swap');"
content = content.replace(old_import, new_import)

# Update headings font family
content = content.replace(
    "h1, h2, h3, h4, h5, h6 {\n        font-family: 'JetBrains Mono', monospace !important;",
    "h1, h2, h3, h4, h5, h6 {\n        font-family: 'Montserrat', sans-serif !important;"
)

# Update .title-text font family
content = content.replace(
    ".title-text {\n        font-family: 'JetBrains Mono', monospace !important;",
    ".title-text {\n        font-family: 'Montserrat', sans-serif !important;"
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated main headings to Montserrat!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Update Font Import
old_import = "@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;700;800&display=swap');"
new_import = "@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap');"
content = content.replace(old_import, new_import)

# Insert specific 'p' styling block before the general p, span, div, label rule
p_rule = """
    p, .stMarkdown p {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 400;
        font-size: 0.95rem;
        line-height: 1.6;
    }
"""
content = content.replace("    p, span, div, label { font-size: 0.95rem; line-height: 1.6; }", p_rule + "\n    span, div, label { font-size: 0.95rem; line-height: 1.6; }")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("DM Sans applied to paragraphs!")
import re

file_path = "frontend/app.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace the entire <style> block
old_style_start = '<style>'
old_style_end = '</style>'
start_idx = content.find(old_style_start)
end_idx = content.find(old_style_end) + len(old_style_end)

new_style = """<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700;800&family=Fira+Code:wght@300;400;500;600;700&display=swap');
    
    html { scroll-behavior: smooth; }
    
    html, body, [class*="css"], .stApp {
        font-family: 'JetBrains Mono', monospace !important;
        background-color: #050505 !important;
        color: #E2E8F0;
        -webkit-font-smoothing: antialiased;
    }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #050505; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #555; }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        letter-spacing: -0.04em;
        text-transform: uppercase;
    }
    h1 { font-size: 2.2rem !important; line-height: 1.1 !important; margin-bottom: 1rem !important; }
    h2 { font-size: 1.7rem !important; line-height: 1.2 !important; margin-bottom: 0.8rem !important; }
    h3 { font-size: 1.3rem !important; line-height: 1.3 !important; }
    h4 { font-size: 1.1rem !important; }
    p, span, div, label { font-size: 0.95rem; line-height: 1.6; }
    
    .clean-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 4px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        animation: fadeIn 0.6s ease-out forwards;
    }
    .clean-card:hover {
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .title-text {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.05em;
        text-transform: uppercase;
        border-bottom: 2px solid #FFFFFF;
        display: inline-block;
        padding-bottom: 4px;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0A0A0B !important;
        border-right: 1px solid #222 !important;
        padding-top: 2rem;
    }
    
    .stSelectbox > div[data-baseweb="select"] > div {
        background-color: #1A1A1C;
        border: 1px solid #333;
        border-radius: 2px;
        color: #E2E8F0;
        font-family: 'JetBrains Mono', monospace !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stSelectbox > div[data-baseweb="select"] > div:hover { border-color: #666; }
    
    .streamlit-expanderHeader {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 2px !important;
        padding: 12px 16px !important;
        transition: all 0.3s ease;
    }
    .streamlit-expanderHeader:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    .streamlit-expanderContent {
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-top: none !important;
        padding: 20px !important;
        animation: slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        background-color: #0A0A0B !important;
    }
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-5px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .contradiction-alert {
        background-color: rgba(255, 50, 50, 0.05);
        border: 1px solid rgba(255, 50, 50, 0.2);
        border-left: 4px solid #FF3333;
        color: #FFB3B3;
        padding: 16px;
        border-radius: 2px;
        margin: 16px 0;
        font-size: 13px;
        font-family: 'JetBrains Mono', monospace;
    }
    .compliance-alert {
        background-color: rgba(255, 170, 0, 0.05);
        border: 1px solid rgba(255, 170, 0, 0.2);
        border-left: 4px solid #FFAA00;
        color: #FFE6B3;
        padding: 16px;
        border-radius: 2px;
        margin: 16px 0;
        font-size: 13px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .persona-banner {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 4px solid #FFFFFF;
        border-radius: 2px;
        padding: 16px 20px;
        margin-bottom: 32px;
        font-size: 13px;
        color: #E2E8F0;
        display: flex;
        align-items: center;
        gap: 12px;
        animation: fadeIn 0.8s ease-out forwards;
    }
    
    div.stButton > button {
        background-color: #FFFFFF;
        color: #000;
        border: 1px solid #FFFFFF;
        border-radius: 2px;
        padding: 8px 24px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: transparent;
        color: #FFFFFF;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid #222;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 1rem;
        padding-bottom: 1rem;
        font-weight: 500;
        color: #666;
        border-bottom-color: transparent !important;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 12px;
        transition: color 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #AAA; }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom: 2px solid #FFFFFF !important;
    }
    </style>"""

content = content[:start_idx] + new_style + content[end_idx:]

# 2. Update inline dark mode styles
replacements = [
    (r'background-color: #FFFFFF; border: 1px solid #EAEAEA;', r'background-color: #0A0A0B; border: 1px solid #333;'),
    (r'border: 1px solid #111111;', r'border: 1px solid #FFFFFF;'),
    (r'stroke="#111111"', r'stroke="#FFFFFF"'),
    (r'color: #111111;', r'color: #FFFFFF;'),
    (r'background: #FAFAFA;', r'background: #111;'),
    (r'background: #111111;', r'background: #FFFFFF; color: #000000;'),
    (r'color: #FFFFFF;', r'color: #000;'), # Button text inversion fix
    (r'color: #6b7280;', r'color: #888;'),
    (r'border-left: 4px solid #111111;', r'border-left: 4px solid #FFFFFF;'),
    (r'background-color: #ffffff; border: 1px solid #e5e7eb;', r'background-color: #0A0A0B; border: 1px solid #333;'),
    (r'color: #333333;', r'color: #E2E8F0;'),
    (r'color:#111111', r'color:#FFFFFF'),
    (r"color: #111111", r"color: #FFFFFF"),
    (r"color: #000000", r"color: #FFFFFF"),
]

for old, new in replacements:
    content = re.sub(old, new, content)

# Special fix for the copy button which we accidentally made color: #000;
content = content.replace("background: #FFFFFF; color: #000000; border: 1px solid #FFFFFF; border-radius: 4px; color: #000;", "background: #FFFFFF; border: 1px solid #FFFFFF; border-radius: 4px; color: #000000;")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated!")
import re

file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_html = "return \"<div style='padding:20px; text-align:center;'>Interactive Graph Visualization (Mocked for UI testing)</div>\""
new_html = "return \"<body style='margin:0; background:#1F1F1F; display:flex; align-items:center; justify-content:center; height:100vh; font-family: \\\"Work Sans\\\", sans-serif; color: #E2E8F0;'><div style='padding:20px; text-align:center; border: 1px dashed #333333; border-radius: 8px;'>Interactive Graph Visualization (Mocked for UI testing)</div></body>\""
content = content.replace(old_html, new_html)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Graph mock HTML fixed!")
import re
file_path = "backend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

if "load_dotenv" not in content:
    content = "from dotenv import load_dotenv\nload_dotenv()\n\n" + content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        print("Injected load_dotenv into src/app.py")
else:
    print("load_dotenv already present in src/app.py")
import re
file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_mermaid = """        er_code = \"\"\"erDiagram
    DOCUMENT ||--o{ PERSON : AUTHORED_BY
    DOCUMENT ||--o{ EQUIPMENT : MENTIONS
    DOCUMENT ||--o{ REGULATION : MENTIONS
    EQUIPMENT ||--o{ FAILURE_MODE : HAS_FAILURE
    EQUIPMENT ||--o{ REGULATION : GOVERNED_BY
    EQUIPMENT ||--o{ PARAMETER : HAS_PARAMETER
    EQUIPMENT ||--o{ DATE : HAS_INSPECTION\"\"\""""

new_mermaid = """        er_code = \"\"\"erDiagram
    DOCUMENT ||--o{ PERSON : "AUTHORED BY"
    DOCUMENT ||--o{ EQUIPMENT : "MENTIONS"
    DOCUMENT ||--o{ REGULATION : "MENTIONS"
    EQUIPMENT ||--o{ "FAILURE_MODE" : "HAS FAILURE"
    EQUIPMENT ||--o{ REGULATION : "GOVERNED BY"
    EQUIPMENT ||--o{ PARAMETER : "HAS PARAMETER"
    EQUIPMENT ||--o{ DATE : "HAS INSPECTION"\"\"\""""

content = content.replace(old_mermaid, new_mermaid)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Mermaid diagram fixed!")
import re
file_path = "frontend/app.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_script = "mermaid.initialize({ startOnLoad: true, theme: 'dark', securityLevel: 'loose' });"
new_script = "mermaid.initialize({ startOnLoad: true, theme: 'base', themeVariables: { fontFamily: 'JetBrains Mono, monospace', primaryColor: '#1F1F1F', primaryTextColor: '#E2E8F0', primaryBorderColor: '#333333', lineColor: '#38BDF8', secondaryColor: '#0A0A0B', tertiaryColor: '#1F1F1F' }, securityLevel: 'loose' });"

# Also update the container background to match the palette 30% instead of #0F172A
old_div = "<div style=\"background-color: #0F172A; padding: 20px; border-radius: 8px; display: flex; justify-content: center; align-items: center; border: 1px solid #334155;\">"
new_div = "<div style=\"background-color: #1F1F1F; padding: 20px; border-radius: 8px; display: flex; justify-content: center; align-items: center; border: 1px dashed #333333;\">"

content = content.replace(old_script, new_script)
content = content.replace(old_div, new_div)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Mermaid styling fixed!")
