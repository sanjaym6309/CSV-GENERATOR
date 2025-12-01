import os
import streamlit as st
import csv
import secrets
import string
import io
import google.generativeai as genai

# 1. Configure Gemini API Key
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("⚠️ Missing Google Generative AI Key! Add it to .streamlit/secrets.toml or environment variables.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

def generate_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

st.set_page_config(page_title="VANO User List CSV Generator", page_icon="📋", layout="wide")
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
