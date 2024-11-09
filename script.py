import io
import os
import pandas as pd
from datetime import datetime
from instagrapi import Client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Load Google Drive credentials from the GitHub Actions secret
SERVICE_ACCOUNT_INFO = os.getenv('GOOGLE_CREDENTIAL')  # Loaded as JSON string from GitHub secrets
credentials = service_account.Credentials.from_service_account_info(
    eval(SERVICE_ACCOUNT_INFO),  # Convert JSON string to dictionary
    scopes=['https://www.googleapis.com/auth/drive']
)

# Build the Google Drive service
service = build('drive', 'v3', credentials=credentials)

# Define the path for session caching
SESSION_FILE_PATH = 'insta_session.json'

def login_with_session(client):
    """
    Login to Instagram using session caching. If a session file exists, it will be loaded;
    otherwise, a new login will be performed, and the session will be saved.
    
    Parameters:
    client (Client): The instagrapi Client instance.
    """
    if os.path.exists(SESSION_FILE_PATH):
        # Load session if available
        client.load_settings(SESSION_FILE_PATH)
        client.relogin()  # Ensures session is still valid
        print("Session loaded successfully")
    else:
        # Login with credentials and save session
        client.login(os.getenv('INSTAGRAM_USERNAME'), os.getenv('INSTAGRAM_PASSWORD'))
        client.dump_settings(SESSION_FILE_PATH)  # Save the session
        print("Logged in and session saved")

def download_file_from_drive(file_name):
    """
    Downloads a file from the specified Google Drive folder "english_skills_101".

    Parameters:
    file_name (str): The name of the file to download from the folder.
    """
    folder_name = "english_skills_101"
    
    # Step 1: Find the folder by name and get its ID
    folder_query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
    folder_results = service.files().list(q=folder_query, fields="files(id, name)").execute()
    folders = folder_results.get('files', [])
    
    if not folders:
        print(f"Folder '{folder_name}' not found.")
        return None
    
    folder_id = folders[0]['id']
    print(f"Found folder '{folder_name}' with ID: {folder_id}")

    # Step 2: Find the file within the specified folder
    file_query = f"name = '{file_name}' and '{folder_id}' in parents"
    file_results = service.files().list(q=file_query, fields="files(id, name)").execute()
    files = file_results.get('files', [])
    
    if not files:
        print(f"File '{file_name}' not found in folder '{folder_name}'.")
        return None
    
    file_id = files[0]['id']
    print(f"Found file '{file_name}' with ID: {file_id}")

    # Step 3: Download the file
    request = service.files().get_media(fileId=file_id)
    file_path = file_name  # Save the file with the same name locally
    with io.FileIO(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%")
    
    print(f"File '{file_name}' downloaded successfully to '{file_path}'.")
    return file_path

def upload_video_and_story(video_path, caption):
    """
    Uploads a video to Instagram as both a post and a story.

    Parameters:
    video_path (str): The file path of the video to upload.
    caption (str): The caption to include with the post.
    """
    # Initialize the Instagram client
    cl = Client()

    # Login using session
    login_with_session(cl)

    # Upload the video as a post
    cl.video_upload(video_path, caption)
    print(f"Video uploaded as a post with caption: {caption}")

    # Upload the video as a story
    cl.video_upload_to_story(video_path)
    print("Video uploaded as a story")

# Load the schedule from the CSV file
schedule_csv_path = 'media_schedule.csv'
schedule_df = pd.read_csv(schedule_csv_path)

# Get today's date
today_date = datetime.now().strftime('%Y-%m-%d')

# Check if there is a media file for today
media_row = schedule_df[schedule_df['Date'] == today_date]

if not media_row.empty:
    file_name = media_row.iloc[0]['File Path']  # Column for file name in the Google Drive folder

    # Download the video file from Google Drive
    media_path = download_file_from_drive(file_name)

    if media_path:
        # Read the caption from caption.txt
        with open('caption.txt', 'r') as caption_file:
            caption = caption_file.read().strip()
        
        # Upload the media if found
        upload_video_and_story(media_path, caption)

        # Clean up the downloaded media file after uploading
        os.remove(media_path)
        print("Temporary media file removed after upload.")
else:
    print("No media scheduled for today")
