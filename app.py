import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image
import io
import json
# ================= CONFIG =================
DRIVE_FOLDER_ID = "1IfbG3x6NE9TQsIu-3eb8hqtvklpMG_J6"
SERVICE_ACCOUNT_FILE = "service_account.json"

SCOPES = ["https://www.googleapis.com/auth/drive"]

# ================= AUTH =================
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["google"], scopes=SCOPES
)

drive_service = build("drive", "v3", credentials=credentials)

# ================= HELPERS =================
def get_or_create_student_folder(roll_no):
    query = (
        f"name='{roll_no}' and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"'{DRIVE_FOLDER_ID}' in parents"
    )

    results = drive_service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    folder_metadata = {
        "name": roll_no,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [DRIVE_FOLDER_ID]
    }

    folder = drive_service.files().create(
        body=folder_metadata, fields="id"
    ).execute()

    return folder["id"]

def upload_image(file, folder_id):
    image = Image.open(file)
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    media = MediaIoBaseUpload(img_bytes, mimetype="image/jpeg")

    file_metadata = {
        "name": file.name,
        "parents": [folder_id]
    }

    drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

# ================= UI =================
st.set_page_config(page_title="Dataset Collection", layout="centered")

st.title("📸 Face Dataset Collection Portal")
st.markdown("**For Academic Project Use Only**")

roll_no = st.text_input("Enter Roll Number (e.g., 22JR1A4228)")

uploaded_files = st.file_uploader(
    "Upload 8–12 face images (front, angles, lighting)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if st.button("Submit"):
    if not roll_no:
        st.error("Please enter Roll Number")
    elif not uploaded_files:
        st.error("Please upload at least one image")
    else:
        with st.spinner("Uploading images..."):
            student_folder_id = get_or_create_student_folder(roll_no)

            for file in uploaded_files:
                upload_image(file, student_folder_id)

        st.success("✅ Images uploaded successfully!")
        st.info("You may close the page now.")
