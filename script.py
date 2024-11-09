import io
import os
import pandas as pd
from datetime import datetime
from instagrapi import Client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def login_with_session(client, username, password, session_file_path):
    """
    Login to Instagram using session caching. If a session file exists, it will be loaded;
    otherwise, a new login will be performed, and the session will be saved.
    
    Parameters:
    client (Client): The instagrapi Client instance.
    username (str): Instagram username.
    password (str): Instagram password.
    session_file_path (str): Path for saving the session file.
    """
    client.username = username
    client.password = password
    if os.path.exists(session_file_path):
        # Load session if available
        client.load_settings(session_file_path)
        try:
            client.relogin()
            print("Session loaded successfully")
            return
        except Exception as e:
            print(f"Relogin failed: {e}, performing a fresh login")
    
    # If relogin fails or session file doesn't exist, perform a fresh login
    client.login(username, password)
    client.dump_settings(session_file_path)
    print("Logged in and session saved")


def download_file_from_drive(service, folder_name, file_name):
    """
    Downloads a file from the specified Google Drive folder.

    Parameters:
    service: Authenticated Google Drive service object.
    folder_name (str): The name of the folder in Google Drive.
    file_name (str): The name of the file to download from the folder.
    
    Returns:
    file_path (str): Path to the downloaded file.
    """
    folder_query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
    folder_results = service.files().list(q=folder_query, fields="files(id, name)").execute()
    folders = folder_results.get('files', [])
    
    if not folders:
        print(f"Folder '{folder_name}' not found.")
        return None
    
    folder_id = folders[0]['id']
    print(f"Found folder '{folder_name}' with ID: {folder_id}")

    file_query = f"name = '{file_name}' and '{folder_id}' in parents"
    file_results = service.files().list(q=file_query, fields="files(id, name)").execute()
    files = file_results.get('files', [])
    
    if not files:
        print(f"File '{file_name}' not found in folder '{folder_name}'.")
        return None
    
    file_id = files[0]['id']
    print(f"Found file '{file_name}' with ID: {file_id}")

    request = service.files().get_media(fileId=file_id)
    file_path = file_name
    with io.FileIO(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%")
    
    print(f"File '{file_name}' downloaded successfully to '{file_path}'.")
    return file_path

def upload_video_and_story(client, video_path, caption, username, password):
    """
    Uploads a video to Instagram as both a post and a story.

    Parameters:
    client (Client): The instagrapi Client instance.
    video_path (str): The file path of the video to upload.
    caption (str): The caption to include with the post.
    username (str): Instagram username.
    password (str): Instagram password.
    """
    login_with_session(client, username, password, session_file_path='insta_session.json')
    
    client.video_upload(video_path, caption)
    print(f"Video uploaded as a post with caption: {caption}")

    client.video_upload_to_story(video_path)
    print("Video uploaded as a story")


# Environment Variables and Authentication

SERVICE_ACCOUNT_INFO = os.getenv('GOOGLE_CREDENTIAL')

# Load Instagram credentials from environment variables

INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

credentials = service_account.Credentials.from_service_account_info(
    eval(SERVICE_ACCOUNT_INFO),
    scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=credentials)

# Instagram session file path
SESSION_FILE_PATH = 'insta_session.json'

# Load media schedule
schedule_csv_path = 'media_schedule.csv'
schedule_df = pd.read_csv(schedule_csv_path)

# Get today's media schedule
today_date = datetime.now().strftime('%Y-%m-%d')
media_row = schedule_df[schedule_df['Date'] == today_date]

# Main execution flow
if not media_row.empty:
    file_name = media_row.iloc[0]['File Path']
    media_path = download_file_from_drive(service, folder_name='english_skills_101', file_name=file_name)

    if media_path:
        with open('caption.txt', 'r') as caption_file:
            caption = caption_file.read().strip()
        
        # Initialize Instagram client and upload video
        instagram_client = Client()
        upload_video_and_story(instagram_client, media_path, caption, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

        # Clean up the downloaded video file
        os.remove(media_path)
        print("Temporary media file removed after upload.")
        
        # Remove the generated .jpg file with the same base name
        jpg_file_path = media_path + '.jpg'
        if os.path.exists(jpg_file_path):
            os.remove(jpg_file_path)
            print(f"Temporary file '{jpg_file_path}' removed after upload.")
else:
    print("No media scheduled for today")
