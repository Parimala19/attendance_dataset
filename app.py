import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from PIL import Image
import io
import json

# ---------------- CONFIG ----------------
SCOPES = ["https://www.googleapis.com/auth/drive"]
DRIVE_FOLDER_ID = "PASTE_YOUR_MAIN_DRIVE_FOLDER_ID"

# ---------------- LOAD SECRETS ----------------
client_config = {
    "web": {
        "client_id": st.secrets["google"]["client_id"],
        "project_id": st.secrets["google"]["project_id"],
        "auth_uri": st.secrets["google"]["auth_uri"],
        "token_uri": st.secrets["google"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["google"]["auth_provider_x509_cert_url"],
        "client_secret": st.secrets["google"]["client_secret"],
        "redirect_uris": st.secrets["google"]["redirect_uris"]
    }
}

# ---------------- AUTH ----------------
if "creds" not in st.session_state:
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=st.secrets["google"]["redirect_uris"][0]
    )

    auth_url, _ = flow.authorization_url(prompt="consent")
    st.markdown(f"### 👉 [Login with Google]({auth_url})")
    st.stop()

if "code" in st.query_params:
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=st.secrets["google"]["redirect_uris"][0]
    )
    flow.fetch_token(code=st.query_params["code"])
    st.session_state["creds"] = flow.credentials
    st.experimental_set_query_params()

drive_service = build("drive", "v3", credentials=st.session_state["creds"])

# ---------------- HELPERS ----------------
def get_or_create_folder(roll_no):
    query = f"name='{roll_no}' and mimeType='application/vnd.google-apps.folder' and '{DRIVE_FOLDER_ID}' in parents"
    res = drive_service.files().list(q=query, fields="files(id)").execute()
    files = res.get("files", [])

    if files:
        return files[0]["id"]

    folder = drive_service.files().create(
        body={
            "name": roll_no,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [DRIVE_FOLDER_ID]
        },
        fields="id"
    ).execute()

    return folder["id"]

def upload_image(bytes_io, name, folder_id):
    media = MediaIoBaseUpload(bytes_io, mimetype="image/jpeg")
    drive_service.files().create(
        body={"name": name, "parents": [folder_id]},
        media_body=media
    ).execute()

# ---------------- UI ----------------
st.title("📸 Dataset Collection Portal")
st.caption("Academic project use only")

roll_no = st.text_input("Enter Roll Number")

camera_img = st.camera_input("Capture photo (recommended)")
uploaded_imgs = st.file_uploader(
    "Or upload images",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if st.button("Submit"):
    if not roll_no:
        st.error("Roll number required")
        st.stop()

    folder_id = get_or_create_folder(roll_no)

    if camera_img:
        upload_image(camera_img, f"{roll_no}_camera.jpg", folder_id)

    for img in uploaded_imgs:
        im = Image.open(img)
        buf = io.BytesIO()
        im.save(buf, format="JPEG")
        buf.seek(0)
        upload_image(buf, img.name, folder_id)

    st.success("✅ Images uploaded successfully")
