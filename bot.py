import os, datetime, requests, json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_video_info():
    # Pick video URL
    with open("videos.txt") as f:
        urls = [l.strip() for l in f if l.strip()]
    day = datetime.datetime.now().timetuple().tm_yday
    idx = day % len(urls)
    print(f"Today's video: {idx + 1} of {len(urls)}")
    return urls[idx]

def get_title_and_description():
    with open("captions.txt") as f:
        lines = [l.strip() for l in f if l.strip()]
    day = datetime.datetime.now().timetuple().tm_yday
    idx = day % len(lines)
    line = lines[idx]
    # Split on | to separate title and description
    # e.g.  "My Title | My description here #tags"
    if "|" in line:
        title, description = line.split("|", 1)
    else:
        title, description = line, line
    return title.strip(), description.strip()

def download_video(url):
    print(f"Downloading video from: {url}")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    path = "video.mp4"
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download complete")
    return path

def get_youtube_client():
    creds_json = os.environ["YOUTUBE_CREDENTIALS"]
    creds_data = json.loads(creds_json)
    creds = Credentials(
        token=creds_data["token"],
        refresh_token=creds_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
    )
    return build("youtube", "v3", credentials=creds)

def upload_video(youtube, video_path, title, description):
    print(f"Uploading: {title}")
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["shorts", "viral", "daily"],
            "categoryId": "22"   # 22 = People & Blogs
        },
        "status": {
            "privacyStatus": "public",   # or "private" / "unlisted"
            "selfDeclaredMadeForKids": False,
        }
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    # Resumable upload — handles large files
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print(f"Upload complete! Video ID: {response['id']}")
    print(f"URL: https://youtube.com/watch?v={response['id']}")
    return response

if __name__ == "__main__":
    video_url            = get_video_info()
    title, description   = get_title_and_description()
    video_path           = download_video(video_url)
    youtube              = get_youtube_client()
    upload_video(youtube, video_path, title, description)