from flask import Flask, request, render_template
import yt_dlp as youtube_dl
from moviepy.editor import VideoFileClip
from flask_mail import Mail, Message
import os
import tempfile
import zipfile

app = Flask(__name__)

# Flask-Mail configuration (replace with your email service details)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your_password'         # Replace with your email password
mail = Mail(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    keyword = request.form['keyword']
    number_of_videos = int(request.form['number'])
    user_email = request.form['email']

    # Create a temporary directory to store video and audio files
    temp_dir = tempfile.mkdtemp()
    audio_clips = []

    try:
        # YDL options to download audio from YouTube
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, 'video_%(id)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': 'C:\ffmpeg-2024-10-17-git-e1d1ba4cbc-essentials_build\ffmpeg-2024-10-17-git-e1d1ba4cbc-essentials_build\bin',  # Specify your ffmpeg path here
            'noplaylist': True,  # Avoid downloading playlists
            'quiet': True,       # Suppress output messages
            'restrictfilenames': True,  # Avoid special characters in filenames
        }

        # Download the videos based on search keyword and process the audio
        for i in range(number_of_videos):
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                # Use a specific video URL for simplicity
                yt_info = ydl.extract_info(f"ytsearch1:{keyword}", download=True)
                video_path = os.path.join(temp_dir, f"video_{yt_info['id']}.mp3")
                
                # Extract the first 15 seconds of audio using MoviePy
                audio_clip = AudioFileClip(video_path).subclip(0, 15)
                audio_file_path = os.path.join(temp_dir, f"audio_{i+1}.mp3")
                audio_clip.write_audiofile(audio_file_path)
                audio_clips.append(audio_file_path)
                audio_clip.close()

        # Create a ZIP file containing the audio clips
        zip_file_path = os.path.join(temp_dir, 'audio_clips.zip')
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for audio_file in audio_clips:
                zipf.write(audio_file, os.path.basename(audio_file))

        # Send the ZIP file to the user's email
        msg = Message('Your Audio Clips ZIP File', sender='your_email@gmail.com', recipients=[user_email])
        msg.body = "Here is the ZIP file containing the audio clips of the first 15 seconds of each video."
        with app.open_resource(zip_file_path) as fp:
            msg.attach('audio_clips.zip', 'application/zip', fp.read())
        mail.send(msg)

        return "ZIP file has been sent to your email!"

    except Exception as e:
        return f"An error occurred: {e}"

    finally:
        # Clean up temporary files
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                os.remove(os.path.join(root, file))
        os.rmdir(temp_dir)

if __name__ == '__main__':
    app.run(debug=True)
