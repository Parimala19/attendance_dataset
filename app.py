import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image
import io

# =========================================================
# CONFIG
# =========================================================
DRIVE_FOLDER_ID = "1IfbG3x6NE9TQsIu-3eb8hqtvklpMG_J6"  # YOUR MAIN DRIVE FOLDER ID
SCOPES = ["https://www.googleapis.com/auth/drive"]

# =========================================================
# GOOGLE DRIVE AUTH (STREAMLIT CLOUD)
# =========================================================
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["google"], scopes=SCOPES
)

drive_service = build("drive", "v3", credentials=credentials)

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def get_or_create_student_folder(roll_no):
    """Create / fetch roll-number-wise folder inside main dataset folder"""
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


def upload_image_to_drive(image_bytes, filename, folder_id):
    """Upload image bytes to Google Drive"""
    media = MediaIoBaseUpload(image_bytes, mimetype="image/jpeg")
    file_metadata = {
        "name": filename,
        "parents": [folder_id]
    }

    drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

# =========================================================
# STREAMLIT UI
# =========================================================
st.set_page_config(page_title="Dataset Collection", layout="centered")

st.title("📸 Face Dataset Collection Portal")
st.markdown("**Academic Project – Camera-based Dataset Collection**")
st.warning("⚠️ Please use a **laptop webcam**. Mobile phones are not recommended.")

roll_no = st.text_input("Enter Roll Number (e.g., 22JR1A4228)")

# Session counter
if "count" not in st.session_state:
    st.session_state.count = 0

# =========================================================
# CAMERA CAPTURE SECTION (PRIMARY)
# =========================================================
st.subheader("📷 Capture Images Using Camera")

camera_image = st.camera_input("Take a picture")

if camera_image and roll_no:
    image = Image.open(camera_image)
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    if st.button("Save Captured Image"):
        folder_id = get_or_create_student_folder(roll_no)
        st.session_state.count += 1

        filename = f"{roll_no}_camera_{st.session_state.count}.jpg"
        upload_image_to_drive(img_bytes, filename, folder_id)

        st.success(f"Image {st.session_state.count} captured and uploaded")

st.info(f"📊 Images captured so far: {st.session_state.count}")

# =========================================================
# FILE UPLOAD SECTION (BACKUP OPTION)
# =========================================================
st.subheader("📁 Upload Images (Backup Option)")

uploaded_files = st.file_uploader(
    "Upload face images if camera is unavailable",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if st.button("Upload Selected Files"):
    if not roll_no:
        st.error("Please enter Roll Number first")
    elif not uploaded_files:
        st.error("Please select images to upload")
    else:
        folder_id = get_or_create_student_folder(roll_no)

        for idx, file in enumerate(uploaded_files, start=1):
            image = Image.open(file)
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            filename = f"{roll_no}_upload_{idx}.jpg"
            upload_image_to_drive(img_bytes, filename, folder_id)

        st.success("✅ Uploaded all selected images successfully")

# =========================================================
# FINAL NOTE
# =========================================================
st.markdown("---")
st.markdown(
    "**Note:** Images are stored securely and used strictly for academic purposes."
)
