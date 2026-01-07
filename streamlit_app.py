import uuid
from datetime import datetime, timezone
import streamlit as st
from supabase import create_client

# 1. Configuration
st.set_page_config(page_title="Public Form", page_icon="📝")

# Load secrets from .streamlit/secrets.toml
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
except FileNotFoundError:
    st.error("Secrets not found. Please ensure .streamlit/secrets.toml exists.")
    st.stop()
except KeyError:
    st.error("Secrets found, but keys are missing. Check SUPABASE_URL and SUPABASE_ANON_KEY.")
    st.stop()

BUCKET = "uploads"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📝 Public Submission Form")

# 2. Form UI with New Fields
with st.form("form"):
    st.subheader("Personal Details")
    
    # Using columns to organize the layout better
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name *")
        nic = st.text_input("NIC Number")
        nationality = st.text_input("Nationality")
    
    with col2:
        alias = st.text_input("Alias / Known As")
        # min_value set to 1900 to allow older birth dates
        dob = st.date_input("Date of Birth", value=None, min_value=datetime(1900, 1, 1))
        email = st.text_input("Email")

    st.subheader("Additional Info")
    note = st.text_area("Note / Comments")
    image = st.file_uploader("Upload Image *", type=["jpg", "jpeg", "png"])
    
    submit = st.form_submit_button("Submit Data")

# 3. Submission Logic
if submit:
    # Validation
    if not name:
        st.error("⚠️ Full Name is required.")
        st.stop()
    if not image:
        st.error("⚠️ Image upload is required.")
        st.stop()

    with st.spinner("Uploading..."):
        try:
            # A. Upload Image to Storage
            data = image.getvalue()  # Get raw bytes
            
            # Create a unique path: Year/Month/Day/UUID.jpg
            path = f"{datetime.now(timezone.utc):%Y/%m/%d}/{uuid.uuid4()}.jpg"

            # FIX: Upload 'data' directly (removed io.BytesIO wrapper)
            supabase.storage.from_(BUCKET).upload(
                path,
                data,
                file_options={"content-type": image.type}
            )

            # Get Public URL
            url = supabase.storage.from_(BUCKET).get_public_url(path)

            # B. Insert Data into Database Table
            # Note: We convert 'dob' to string to ensure JSON compatibility
            dob_str = str(dob) if dob else None

            supabase.table("submissions").insert({
                "full_name": name,
                "nic": nic,
                "nationality": nationality,
                "alias": alias,
                "dob": dob_str,
                "email": email,
                "note": note,
                "image_path": path,
                "image_url": url
            }).execute()

            st.success("✅ Submitted Successfully!")
            st.balloons()

        except Exception as e:
            st.error(f"An error occurred: {e}")