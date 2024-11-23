import io
import os
import random
import pandas as pd
from datetime import datetime, timezone
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
            return client
        except Exception as e:
            print(f"Relogin failed: {e}, performing a fresh login")

    # If relogin fails or session file doesn't exist, perform a fresh login
    client.login(username, password)
    client.dump_settings(session_file_path)
    print("Logged in and session saved")
    return client


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


def upload_video_and_story(client, video_path, caption):
    """
    Uploads a video to Instagram as both a post and a story.

    Parameters:
    client (Client): The instagrapi Client instance.
    video_path (str): The file path of the video to upload.
    caption (str): The caption to include with the post.
    """
    client.video_upload(video_path, caption)
    print(f"Video uploaded as a post with caption: {caption}")

    client.video_upload_to_story(video_path)
    print("Video uploaded as a story")


def get_closest_media_row(schedule_csv_path):
    # Load the media schedule
    schedule_df = pd.read_csv(schedule_csv_path)

    # Convert 'Date & Time' column to datetime format and make it timezone-aware in UTC
    schedule_df['Date & Time'] = pd.to_datetime(schedule_df['Date & Time']).dt.tz_localize('UTC')

    # Get current time in UTC
    current_time_utc = datetime.now(timezone.utc)

    # Calculate the absolute time delta and find the row with the minimum difference
    schedule_df['Time Delta'] = (schedule_df['Date & Time'] - current_time_utc).abs()
    closest_media_row = schedule_df.loc[schedule_df['Time Delta'].idxmin()]

    return closest_media_row


def get_random_likers_from_targets(target_usernames, cl):
    """
    Randomly selects a target username from the input list, fetches their top 10 posts,
    randomly selects one post, and returns the list of usernames who liked that post.

    Args:
        target_usernames (list): List of Instagram usernames to choose from.
        cl (Client): An authenticated instagrapi Client instance.

    Returns:
        list: List of usernames who liked the randomly selected post.
    """
    try:
        target_username = random.choice(target_usernames)
        print(f"Randomly selected username: {target_username}")

        user_id = cl.user_id_from_username(target_username)
        print(f"User ID for {target_username}: {user_id}")

        media_list = cl.user_medias(user_id, amount=10)
        if not media_list:
            print(f"No posts found for {target_username}")
            return []

        random_post = random.choice(media_list)
        print(f"Selected media: {random_post.pk}, URL: {random_post.thumbnail_url}")

        likers = cl.media_likers(random_post.pk)
        return [liker.username for liker in likers][:10]
    except Exception as e:
        print(f"Error fetching likers: {e}")
        return []


def process_usernames(usernames, cl):
    """
    Processes a list of Instagram usernames:
    - Checks if the account is public or private.
    - If public and has >4 posts, likes the first 4 posts.

    Args:
        usernames (list): List of Instagram usernames.
        cl (Client): Authenticated instagrapi Client instance.
    """
    for user in usernames:
        try:
            user_info = cl.user_info_by_username(user)
            if not user_info.is_private and user_info.media_count > 4:
                print(f"Processing public user: {user}")
                media_list = cl.user_medias(user_info.pk, amount=4)
                for media in media_list:
                    cl.media_like(media.pk)
                    print(f"Liked post: {media.pk}")
        except Exception as e:
            print(f"Error processing user {user}: {e}")


# Main execution
if __name__ == "__main__":
    # Load environment variables or credentials
    INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
    INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
    # Authenticate Google Drive client
    SERVICE_ACCOUNT_INFO = os.getenv('GOOGLE_CREDENTIAL')
    
    SESSION_FILE_PATH = 'insta_session.json'

    # Authenticate Instagram client
    instagram_client = Client()
    instagram_client = login_with_session(instagram_client, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, SESSION_FILE_PATH)


    credentials = service_account.Credentials.from_service_account_info(
        eval(SERVICE_ACCOUNT_INFO),
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=credentials)

    # Process the media schedule
    media_row = get_closest_media_row('media_schedule.csv')
    if not media_row.empty:
        file_name = media_row['File Path']
        caption = media_row["Caption"]
        media_path = download_file_from_drive(service, folder_name='english_skills_101', file_name=file_name)

        if media_path:
            upload_video_and_story(instagram_client, media_path, caption)
            os.remove(media_path)
            jpg_file_path = media_path + '.jpg'
            if os.path.exists(jpg_file_path):
                os.remove(jpg_file_path)
            
            target_usernames = ["howimetyourmotherthefanpage", "itstedntracy", "himymfeeds", "himymaddiict", "friendsadiction"]
            usernames = get_random_likers_from_targets(target_usernames, instagram_client)

            if usernames:
                instagram_client = Client()
                instagram_client = login_with_session(instagram_client, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, SESSION_FILE_PATH)
                process_usernames(usernames, instagram_client)

