import os
import streamlit as st
import csv
import secrets
import string
import io
import google.generativeai as genai


# -----------------------------
# 1. Configure Gemini API Key
# -----------------------------
st.set_page_config(page_title="VANO User List CSV Generator", page_icon="📋", layout="wide")

st.sidebar.header("🔐 Gemini API Key Settings")

# Your default (owner) key from env or secrets
DEFAULT_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", None)

# User-entered key (masked)
user_api_key = st.sidebar.text_input(
    "Enter your Gemini API Key",
    type="password",
    placeholder="Paste your key here",
    help="Optional: If left empty, the app will use the default built‑in API key."
)

# Button to open Google AI Studio API key dashboard
st.sidebar.link_button(
    "🔑 Get Gemini API Key",
    "https://aistudio.google.com/app/apikey",
    help="Opens Google AI Studio where you can generate and manage your API keys."
)

# Instructions
st.sidebar.markdown(
    """
**Instructions**

1. Click **"Get / Manage Gemini API Key"** to open Google AI Studio.
2. Sign in with your Google account.
3. Create or copy an existing Gemini API key.
4. Paste the key into the field above.
5. If you do **not** enter anything, the app will use the default API key configured on the server.
"""
)

# Final key selection: user key first, otherwise default
GOOGLE_API_KEY = user_api_key.strip() if user_api_key.strip() else DEFAULT_GOOGLE_API_KEY

if not GOOGLE_API_KEY:
    st.error(
        "⚠️ No Gemini API key available.\n\n"
        "Either:\n"
        "- Set GOOGLE_API_KEY in environment variables or `.streamlit/secrets.toml`, **or**\n"
        "- Paste a key in the sidebar input."
    )
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)


def generate_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))


st.title("📋 VANO User List CSV Generator")

# UI
vano_start = st.number_input("VANO Starting Number", min_value=1, value=1, step=1)
vano_end = st.number_input("VANO Ending Number", min_value=1, value=2, step=1)
department = st.text_input("Department", value="BSC")
role = st.selectbox("Role", ["teacher", "student"])
comment = st.text_area("General Instruction (e.g. don't add user 610)", value="")

# Validation
user_count = vano_end - vano_start + 1
validation_failed = False

if vano_start >= vano_end:
    st.error("Starting value must be smaller than ending value.")
    validation_failed = True
elif not comment.strip() and user_count > 50000:
    st.error("You can only generate up to 50,000 users in one batch without AI.")
    validation_failed = True
elif comment.strip() and user_count > 290:
    st.error("AI editing only supports up to 290 users in one batch.")
    validation_failed = True

if not validation_failed and st.button("Generate CSV"):
    # Generate initial CSV
    csv_rows = []
    if comment:
        csv_rows.append([f"# {comment}"])
    csv_rows.append(["name", "email", "password", "role", "department"])

    for vano in range(vano_start, vano_end + 1):
        name = str(vano)
        email = f"{vano}@velsrscollege.com"
        password = generate_password()
        csv_rows.append([name, email, password, role, department])

    output = io.StringIO()
    writer = csv.writer(output)
    for row in csv_rows:
        writer.writerow(row)
    csv_data = output.getvalue()

    # Show download button first
    if not comment.strip():
        st.download_button("💾 Download CSV", csv_data, "user_list.csv", "text/csv")
        st.success("✅ CSV generated successfully (without Gemini AI).")
        st.markdown("#### 🔎 Preview (optional)")
        st.code(csv_data, language='csv')
    else:
        # Gemini AI edit
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        prompt = f"""You are an expert CSV editor.
Here is a user list CSV:
{csv_data}

Apply this instruction: {comment}
Output ONLY the full edited CSV - do not add any explanation."""
        with st.spinner("Gemini AI is processing your instruction..."):
            response = model.generate_content(prompt)
            edited_csv = response.text.strip()
        st.download_button("💾 Download CSV", edited_csv, "user_list_ai.csv", "text/csv")
        st.markdown("#### 🔎 Edited CSV Preview (optional)")
        st.code(edited_csv, language='csv')
else:
    st.info("👆 Enter details and click Generate CSV to begin.")

