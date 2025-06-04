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
</style>
""", unsafe_allow_html=True)

def load_google_sheet(sheet_url):
    """Load data from Google Sheets URL"""
    try:
        # Convert Google Sheets URL to CSV export URL
        if 'docs.google.com/spreadsheets' in sheet_url:
            # Extract sheet ID from URL
            sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            
            # Read the CSV data
            df = pd.read_csv(csv_url)
            return df
        else:
            st.error("Please provide a valid Google Sheets URL")
            return None
    except Exception as e:
        st.error(f"Error loading Google Sheet: {str(e)}")
        return None

def generate_lyrics_with_claude(dreams_list, api_key):
    """Generate song lyrics using Claude Sonnet API"""
    
    # Combine all dreams into a single prompt
    dreams_text = "\n".join([f"- {dream}" for dream in dreams_list])
    
    prompt = f"""You are a creative songwriter tasked with creating beautiful, inspiring song lyrics about Singapore's river and people's dreams connected to it.

Here are the dreams and wishes from various people about Singapore's river:

{dreams_text}

Please create original 2-minute song lyrics that:
1. Weave together the essence and themes from these dreams
2. Celebrate Singapore's river and its meaning to people
3. Are uplifting and inspiring
4. Have a clear verse-chorus structure suitable for singing
5. Capture the multicultural spirit of Singapore
6. Include imagery of water, hopes, and community

The lyrics should be completely original and suitable for a 2-minute song. Please format with clear verse and chorus sections."""

    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01'
    }
    
    data = {
        'model': 'claude-3-5-sonnet-20241022',
        'max_tokens': 1000,
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

def generate_song_with_suno(lyrics, api_key, title="Singapore River Dreams", genre="pop", callback_url=None):
    """Generate song using Suno API"""
    
    # Suno API endpoint from documentation
    suno_url = "https://apibox.erweima.ai/api/v1/generate"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Prepare the request data for Suno using Custom Mode
    # We'll use custom mode with lyrics as the prompt
    callback_endpoint = callback_url if callback_url else 'https://temp-callback-url.example.com'
    
    data = {
        'prompt': lyrics,  # The lyrics will be used as the prompt
        'style': genre,    # Music style/genre
        'title': title,    # Song title
        'customMode': True,    # Enable custom mode for precise control
        'instrumental': False, # We want vocals with lyrics
        'model': 'V4',        # Use V4 for best audio quality
        'negativeTags': 'Heavy Metal, Aggressive',  # Avoid harsh styles
        'callBackUrl': callback_endpoint
    }
    
    try:
        # Make request to Suno API
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

def check_suno_status(task_id, api_key):
    """Check the status of Suno song generation using task details endpoint"""
    
    # Note: You may need to implement the status check endpoint
    # The documentation shows callbacks but doesn't specify a status check endpoint
    # This is a placeholder implementation
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # This endpoint might need to be confirmed based on additional Suno documentation
        response = requests.get(f"https://apibox.erweima.ai/api/v1/task/{task_id}", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                return result
        return None
            
    except Exception as e:
        st.error(f"Error checking Suno status: {str(e)}")
        return None

def main():
    st.markdown("<h1 class='main-header'>🎵 Singapore River Dreams Song Generator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em; color: #666;'>Transform collective dreams about Singapore's river into beautiful songs</p>", unsafe_allow_html=True)
    
    # Sidebar for API keys
    st.sidebar.header("🔑 API Configuration")
    claude_api_key = st.sidebar.text_input("Claude API Key", type="password", help="Enter your Anthropic Claude API key")
    suno_api_key = st.sidebar.text_input("Suno API Key", type="password", help="Enter your Suno API key")
    
    # Add callback URL configuration for production use
    st.sidebar.header("⚙️ Advanced Settings")
    callback_url = st.sidebar.text_input(
        "Callback URL (Optional)", 
        placeholder="https://yourserver.com/callback",
        help="URL to receive completion notifications. Leave empty for demo mode."
    )
    
    # Add preview link in sidebar
    st.sidebar.header("🎧 Song Preview")
    st.sidebar.markdown("""
    <div class="preview-box">
        <strong>🎵 Preview Your Generated Songs</strong><br>
        After generating a song, you can preview and download it using the Suno API logs:
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
        st.header("📊 Input Data")
        
        # Google Sheets input
        st.subheader("Google Sheets URL")
        sheet_url = st.text_input(
            "Enter Google Sheets URL containing dreams about Singapore's river:",
            placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/edit#gid=0",
            help="Make sure your Google Sheet is publicly accessible or shared with viewing permissions"
        )
        
        # Load and display data
        if sheet_url and st.button("📥 Load Dreams from Google Sheet"):
            with st.spinner("Loading dreams from Google Sheet..."):
                df = load_google_sheet(sheet_url)
                
                if df is not None:
                    st.session_state.dreams_df = df
                    st.success(f"✅ Successfully loaded {len(df)} entries!")
        
        # Display loaded data
        if 'dreams_df' in st.session_state:
            st.subheader("📋 Loaded Dreams")
            st.dataframe(st.session_state.dreams_df, use_container_width=True)
            
            # Show sample dreams
            if len(st.session_state.dreams_df) > 0:
                st.subheader("🌟 Sample Dreams")
                dream_column = st.selectbox("Select the column containing dreams:", st.session_state.dreams_df.columns)
                
                sample_dreams = st.session_state.dreams_df[dream_column].dropna().head(3)
                for i, dream in enumerate(sample_dreams, 1):
                    st.markdown(f'<div class="dream-box"><strong>Dream {i}:</strong> {dream}</div>', unsafe_allow_html=True)
    
    with col2:
        st.header("🎼 Song Generation")
        
        if 'dreams_df' in st.session_state and claude_api_key and suno_api_key:
            dream_column = st.selectbox("Select dream column:", st.session_state.dreams_df.columns, key="dream_col_select")
            song_title = st.text_input("Song Title", value="Singapore River Dreams")
            genre = st.selectbox("Music Genre", ["pop", "folk", "indie", "acoustic", "classical", "electronic"])
            
            if st.button("🎵 Generate Song"):
                # Extract dreams from dataframe
                dreams_list = st.session_state.dreams_df[dream_column].dropna().tolist()
                
                if dreams_list:
                    # Step 1: Generate lyrics with Claude
                    st.subheader("✍️ Generating Lyrics...")
                    with st.spinner("Claude is crafting beautiful lyrics from the dreams..."):
                        lyrics = generate_lyrics_with_claude(dreams_list, claude_api_key)
                    
                    if lyrics:
                        st.markdown('<div class="success-box">✅ Lyrics generated successfully!</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="lyrics-box"><h4>🎼 Generated Lyrics:</h4><pre>{lyrics}</pre></div>', unsafe_allow_html=True)
                        
                        # Step 2: Generate song with Suno
                        st.subheader("🎵 Creating Song...")
                        with st.spinner("Suno is composing your song... This might take a few minutes."):
                            suno_result = generate_song_with_suno(lyrics, suno_api_key, song_title, genre, callback_url)
                        
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
                                    
                                    # Enhanced preview section with direct link
                                    st.markdown("""
                                    <div class="preview-box">
                                        <h4>🎧 Preview Your Song</h4>
                                        <p>Your song is being generated! Once complete (usually 2-5 minutes), you can preview and download it:</p>
                                        <a href="https://sunoapi.org/logs" target="_blank" class="link-button">
                                            🔗 Open Suno API Logs to Preview
                                        </a>
                                        <br><br>
                                        <strong>📋 Your Task ID:</strong> <code>{}</code>
                                        <br><br>
                                        <small>💡 <strong>How to find your song:</strong></small>
                                        <ul>
                                            <li>Click the link above to open Suno API logs</li>
                                            <li>Search for your Task ID: <code>{}</code></li>
                                            <li>Once generation is complete, you'll see audio download links</li>
                                            <li>Click to listen and download your song!</li>
                                        </ul>
                                    </div>
                                    """.format(task_id, task_id), unsafe_allow_html=True)
                                    
                                    # Progress estimation
                                    st.subheader("⏳ Generation Progress")
                                    progress_bar = st.progress(0)
                                    status_text = st.empty()
                                    
                                    # Simulate progress (since we can't get real-time status)
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
                                    
                                    # Additional information
                                    st.markdown("""
                                    <div style="background-color: #fff3cd; padding: 1rem; border-radius: 10px; border-left: 4px solid #ffc107; margin-top: 1rem;">
                                    <strong>⏳ What happens next?</strong><br>
                                    <ul>
                                        <li>🎵 Suno AI is now composing your song (2-5 minutes)</li>
                                        <li>🔗 Use the link above to check progress and download when ready</li>
                                        <li>📧 If you provided a callback URL, you'll receive a notification</li>
                                        <li>🎧 Generated songs typically include multiple variations to choose from</li>
                                    </ul>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # For demo purposes, show what the callback would contain
                                    st.subheader("📋 Expected Result Structure")
                                    st.json({
                                        "message": "When complete, you'll receive:",
                                        "structure": {
                                            "audio_url": "Direct link to download the MP3",
                                            "stream_audio_url": "Link for streaming",
                                            "image_url": "Album cover/artwork",
                                            "title": song_title,
                                            "duration": "Song length in seconds",
                                            "model_name": "AI model used"
                                        }
                                    })
                            
                            # Show the API response for debugging
                            with st.expander("🔍 API Response Details"):
                                st.json(suno_result)
                                
                else:
                    st.warning("No dreams found in the selected column.")
        
        elif not claude_api_key or not suno_api_key:
            st.info("👈 Please enter your API keys in the sidebar to start generating songs.")
        
        else:
            st.info("👈 Please load dreams from Google Sheets first.")
    
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
