import streamlit as st
import pandas as pd
import requests
import json
import time
from io import StringIO
import base64

# Set page config
st.set_page_config(
    page_title="Singapore River Dreams Song Generator",
    page_icon="🎵",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .dream-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .lyrics-box {
        background-color: #e8f4f8;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        font-family: 'Georgia', serif;
        line-height: 1.6;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
    }
    .preview-box {
        background-color: #e7f3ff;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    .link-button {
        display: inline-block;
        padding: 0.5rem 1rem;
        background-color: #007bff;
        color: white;
        text-decoration: none;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .link-button:hover {
        background-color: #0056b3;
        color: white;
        text-decoration: none;
    }
    .config-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Fixed Google Sheets URL
FIXED_SHEET_URL = "https://docs.google.com/spreadsheets/d/1CRmG9M841oGGJjT8ks4b-2zR0vrFy0tHCMf_099Zxf0/edit?resourcekey=&gid=322702448#gid=322702448"

def load_dreams_from_fixed_sheet():
    """Load dreams from the fixed Google Sheets URL"""
    try:
        # Convert Google Sheets URL to CSV export URL
        sheet_id = "19uPq9pUeJdYPwiUqvI2VvlHSXk_BE3ccrkR6eNY-n50"
        gid = "1092449549"
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        
        # Read the CSV data
        df = pd.read_csv(csv_url)
        
        # Extract only the dreams column (second column - "What is your dream")
        if len(df.columns) >= 2:
            dreams_column = df.columns[1]  # Second column
            dreams_list = df[dreams_column].dropna().tolist()
            return dreams_list, df
        else:
            st.error("The spreadsheet doesn't have the expected columns")
            return [], None
            
    except Exception as e:
        st.error(f"Error loading dreams from Google Sheet: {str(e)}")
        return [], None

def generate_simple_lyrics(dreams_list, api_key):
    """Generate simple 2-minute song lyrics using Claude API"""
    
    # Simple prompt as requested
    dreams_text = "\n".join([f"- {dream}" for dream in dreams_list[:20]])  # Limit to first 20 dreams
    
    prompt = f"""Create 2-minute song lyrics that incorporates all the following dreams substracting any hate or bad words or dreams:

{dreams_text}

Make the lyrics inspiring and cohesive. Structure it with verses and chorus."""

    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01'
    }
    
    data = {
        'model': 'claude-3-5-sonnet-20241022',
        'max_tokens': 800,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }
    
    try:
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['content'][0]['text']
        else:
            st.error(f"Claude API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error calling Claude API: {str(e)}")
        return None

def generate_song_with_suno(lyrics, suno_config):
    """Generate song using Suno API with user preferences"""
    
    suno_url = "https://apibox.erweima.ai/api/v1/generate"
    
    headers = {
        'Authorization': f'Bearer {suno_config["api_key"]}',
        'Content-Type': 'application/json'
    }
    
    # Build style string based on preferences
    style_parts = [suno_config["genre"]]
    
    if suno_config["vocal_type"] != "Mixed":
        style_parts.append(suno_config["vocal_type"])
    
    if suno_config["additional_style"]:
        style_parts.append(suno_config["additional_style"])
    
    style_string = ", ".join(style_parts)
    
    # Prepare the request data
    data = {
        'prompt': lyrics if not suno_config["instrumental"] else suno_config.get("description", "Instrumental track based on dreams"),
        'style': style_string,
        'title': suno_config["title"],
        'customMode': True,
        'instrumental': suno_config["instrumental"],
        'model': suno_config["model"],
        'negativeTags': suno_config["negative_tags"],
        'callBackUrl': suno_config["callback_url"]
    }
    
    try:
        response = requests.post(suno_url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                return result
            else:
                st.error(f"Suno API Error: {result.get('msg', 'Unknown error')}")
                return None
        else:
            st.error(f"Suno API HTTP Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error calling Suno API: {str(e)}")
        return None

def main():
    st.markdown("<h1 class='main-header'>🎵 Singapore River Dreams Song Generator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em; color: #666;'>Transform collective dreams about Singapore's river into beautiful songs</p>", unsafe_allow_html=True)
    
    # Display the fixed spreadsheet link
    st.markdown(f"""
    <div class="preview-box">
        <h4>📊 Dreams Data Source</h4>
        <p>This app uses a fixed Google Spreadsheet containing dreams about Singapore's river:</p>
        <a href="{FIXED_SHEET_URL}" target="_blank" class="link-button">
            🔗 View Dreams Spreadsheet
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for API keys
    st.sidebar.header("🔑 API Configuration")
    claude_api_key = st.sidebar.text_input("Claude API Key", type="password", help="Enter your Anthropic Claude API key")
    suno_api_key = st.sidebar.text_input("Suno API Key", type="password", help="Enter your Suno API key")
    
    # Suno Configuration in Sidebar
    st.sidebar.header("🎵 Suno Music Preferences")
    
    song_title = st.sidebar.text_input("Song Title", value="Singapore River Dreams", max_chars=80)
    
    model_version = st.sidebar.selectbox(
        "Model Version",
        ["V4_5", "V4", "V3_5"],
        index=0,
        help="V4_5: Up to 8min, superior blending | V4: Best quality, 4min | V3_5: Creative diversity, 4min"
    )
    
    genre = st.sidebar.selectbox(
        "Primary Genre",
        ["Pop", "Folk", "Indie", "Acoustic", "Classical", "Electronic", "Rock", "Jazz", "R&B", "Country"]
    )
    
    vocal_type = st.sidebar.selectbox(
        "Vocal Preference",
        ["Mixed", "Male Singer", "Female Singer"],
        help="Choose the preferred vocal type for the song"
    )
    
    instrumental_only = st.sidebar.checkbox("Instrumental Only", help="Generate instrumental music without vocals")
    
    additional_style = st.sidebar.text_input(
        "Additional Style Elements",
        placeholder="e.g., Uplifting, Dreamy, Inspirational",
        help="Add extra style descriptors (optional)"
    )
    
    negative_tags = st.sidebar.text_input(
        "Styles to Avoid",
        value="Heavy Metal, Aggressive, Dark",
        help="Musical styles or traits to exclude from generation"
    )
    
    callback_url = st.sidebar.text_input(
        "Callback URL",
        value="https://api.example.com/callback",
        help="URL to receive completion notifications"
    )
    
    # Add preview link in sidebar
    st.sidebar.header("🎧 Song Preview")
    st.sidebar.markdown("""
    <div class="preview-box">
        <strong>🎵 Preview Your Generated Songs</strong><br>
        After generating a song, you can preview and download it:
        <br><br>
        <a href="https://sunoapi.org/logs" target="_blank" class="link-button">
            🔗 Open Suno API Logs
        </a>
        <br><br>
        <small>Use your task ID to find your generated songs in the logs.</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📊 Dreams Data")
        
        # Load dreams from fixed sheet
        if st.button("📥 Load Dreams from Spreadsheet", type="primary"):
            with st.spinner("Loading dreams from the fixed Google Sheet..."):
                dreams_list, df = load_dreams_from_fixed_sheet()
                
                if dreams_list:
                    st.session_state.dreams_list = dreams_list
                    st.session_state.dreams_df = df
                    st.success(f"✅ Successfully loaded {len(dreams_list)} dreams!")
                    
                    # Show sample dreams
                    st.subheader("🌟 Sample Dreams")
                    for i, dream in enumerate(dreams_list[:5], 1):
                        st.markdown(f'<div class="dream-box"><strong>Dream {i}:</strong> {dream}</div>', unsafe_allow_html=True)
                    
                    if len(dreams_list) > 5:
                        st.info(f"And {len(dreams_list) - 5} more dreams...")
        
        # Display loaded data
        if 'dreams_df' in st.session_state:
            st.subheader("📋 Full Dataset")
            st.dataframe(st.session_state.dreams_df, use_container_width=True)
    
    with col2:
        st.header("🎼 Song Generation")
        
        # Configuration summary
        if suno_api_key:
            st.markdown(f"""
            <div class="config-section">
                <h4>🎵 Current Configuration</h4>
                <ul>
                    <li><strong>Title:</strong> {song_title}</li>
                    <li><strong>Model:</strong> {model_version}</li>
                    <li><strong>Genre:</strong> {genre}</li>
                    <li><strong>Vocals:</strong> {"Instrumental Only" if instrumental_only else vocal_type}</li>
                    <li><strong>Style:</strong> {additional_style if additional_style else "Default"}</li>
                    <li><strong>Avoid:</strong> {negative_tags}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        if 'dreams_list' in st.session_state and claude_api_key and suno_api_key:
            if st.button("🎵 Generate Song", type="primary"):
                dreams_list = st.session_state.dreams_list
                
                # Step 1: Generate lyrics with Claude
                st.subheader("✍️ Generating Lyrics...")
                with st.spinner("Claude is creating lyrics from all the dreams..."):
                    lyrics = generate_simple_lyrics(dreams_list, claude_api_key)
                
                if lyrics:
                    st.markdown('<div class="success-box">✅ Lyrics generated successfully!</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="lyrics-box"><h4>🎼 Generated Lyrics:</h4><pre>{lyrics}</pre></div>', unsafe_allow_html=True)
                    
                    # Step 2: Generate song with Suno
                    st.subheader("🎵 Creating Song...")
                    
                    # Prepare Suno configuration
                    suno_config = {
                        "api_key": suno_api_key,
                        "title": song_title,
                        "genre": genre,
                        "vocal_type": vocal_type,
                        "additional_style": additional_style,
                        "instrumental": instrumental_only,
                        "model": model_version,
                        "negative_tags": negative_tags,
                        "callback_url": callback_url
                    }
                    
                    with st.spinner("Suno is composing your song... This might take a few minutes."):
                        suno_result = generate_song_with_suno(lyrics, suno_config)
                    
                    if suno_result:
                        st.markdown('<div class="success-box">✅ Song generation request sent successfully!</div>', unsafe_allow_html=True)
                        
                        # Store results in session state
                        st.session_state.lyrics = lyrics
                        st.session_state.suno_result = suno_result
                        
                        # Display task information
                        if 'data' in suno_result:
                            task_id = suno_result['data'].get('task_id')
                            if task_id:
                                st.info(f"🎵 Task ID: {task_id}")
                                
                                # Enhanced preview section
                                st.markdown(f"""
                                <div class="preview-box">
                                    <h4>🎧 Preview Your Song</h4>
                                    <p>Your song is being generated! Once complete (usually 2-5 minutes), you can preview and download it:</p>
                                    <a href="https://sunoapi.org/logs" target="_blank" class="link-button">
                                        🔗 Open Suno API Logs to Preview
                                    </a>
                                    <br><br>
                                    <strong>📋 Your Task ID:</strong> <code>{task_id}</code>
                                    <br><br>
                                    <small>💡 <strong>How to find your song:</strong></small>
                                    <ul>
                                        <li>Click the link above to open Suno API logs</li>
                                        <li>Search for your Task ID: <code>{task_id}</code></li>
                                        <li>Once generation is complete, you'll see audio download links</li>
                                        <li>Click to listen and download your song!</li>
                                    </ul>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Progress estimation
                                st.subheader("⏳ Generation Progress")
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                # Simulate progress
                                for i in range(0, 101, 5):
                                    progress_bar.progress(i)
                                    if i < 30:
                                        status_text.text(f"🎵 Analyzing lyrics and creating musical arrangement... {i}%")
                                    elif i < 60:
                                        status_text.text(f"🎤 Generating vocals and melody... {i}%")
                                    elif i < 90:
                                        status_text.text(f"🎚️ Mixing and mastering audio... {i}%")
                                    else:
                                        status_text.text(f"✨ Finalizing your song... {i}%")
                                    time.sleep(0.1)
                                
                                status_text.text("🎉 Generation process initiated! Check the Suno API logs for completion.")
                        
                        # Show the API response for debugging
                        with st.expander("🔍 API Response Details"):
                            st.json(suno_result)
        
        elif not claude_api_key or not suno_api_key:
            st.info("👈 Please enter your API keys in the sidebar to start generating songs.")
        
        elif 'dreams_list' not in st.session_state:
            st.info("👈 Please load dreams from the spreadsheet first.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666; font-size: 0.9em;'>"
        "🌊 Bringing Singapore's river dreams to life through music 🎵"
        "</p>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
