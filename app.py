import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import datetime
import os
from datetime import datetime
from dotenv import load_dotenv
import dropbox
import requests 

# Load environment variables
load_dotenv()

# Fetch credentials from environment variables
VALID_USERNAME = os.getenv("APP_USERNAME")
VALID_PASSWORD = os.getenv("APP_PASSWORD")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")



data_file = "receipts.csv"

def get_access_token():
    """Fetches a new Dropbox access token using the refresh token."""
    response = requests.post("https://api.dropbox.com/oauth2/token", data={
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_APP_KEY,
        "client_secret": DROPBOX_APP_SECRET
    })
    return response.json().get("access_token")

def upload_to_dropbox(file_bytes, dropbox_path):
    """Uploads a file to Dropbox"""
    access_token = get_access_token()
    dbx = dropbox.Dropbox(access_token)

    try:
        dbx.files_upload(file_bytes.getvalue(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
        shared_link = dbx.sharing_create_shared_link(dropbox_path).url
        return shared_link  # Return Dropbox file link
    except Exception as e:
        print(f"Dropbox Upload Error: {e}")
        return None
        
def save_to_csv(data):
    df = pd.DataFrame([data])
    if not os.path.exists(data_file):
        df.to_csv(data_file, index=False)
        
    else:
        df.to_csv(data_file, mode='a', header=False, index=False)

def generate_receipt(receipt_number, student_name, date, amount_paid, fee_type, month, logo_path):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    if logo_path:
        try:
            c.drawImage(logo_path, 40, height - 80, width=100, height=50, preserveAspectRatio=True, mask='auto')
        except:
            pass  
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(230, height - 50, "RECEIPT")
    
    c.setFont("Helvetica", 12)
    c.drawString(400, height - 80, f"Receipt #: {receipt_number}")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 120, "FROM")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 140, "NEETPrep Shantiniketan")
    c.drawString(50, height - 155, "Astha Complex, Sriniketan Rd (near Bolpur High School)")
    c.drawString(50, height - 170, "Bolpur, West Bengal 731204")
    
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(166/255, 166/255, 166/255) 
    c.drawString(50, height - 200, f"BILL TO - {student_name}")
    c.setFillColorRGB(0, 0, 0)  # Reset color to black for other text

    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(166/255, 166/255, 166/255) 
    c.drawString(50, height - 230, "DATE")
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 245, date)

    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(166/255, 166/255, 166/255) 
    c.drawString(400, height - 230, "BALANCE PAID")
    c.setFillColorRGB(0, 0, 0)

    c.setFillColorRGB(46/255, 117/255, 181/255)
    c.setFont("Helvetica", 15)
    c.drawString(400, height - 245, f"₹ {amount_paid:.2f}")
    c.setFillColorRGB(0, 0, 0)  # Reset color to black for other text

    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 280, "DESCRIPTION")
    c.drawString(450, height - 280, "TOTAL")
    
    c.setFont("Helvetica", 10)
    description = fee_type if fee_type == "Admission Fee" else f"Tuition Fees: ({month})"
    c.drawString(50, height - 300, description)
    c.drawString(450, height - 300, f"₹ {amount_paid:.2f}")
        
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 370, "Thank you for joining NEETPrep.")
    c.setFillColorRGB(0, 0, 1)  # Set text color to blue
    url = "https://www.neetprep.com/"
    c.drawString(50, height - 385, url)
    c.linkURL(url, (50, height - 395, 350, height - 380), relative=1)
    c.setFillColorRGB(0, 0, 0)  # Reset color to black for other text

    
    c.setFont("Helvetica", 70)
    c.setFillAlpha(0.1)
    c.drawString(130, height / 2, "NEETPrep")

    # Save PDF in structured folders
    year_month = datetime.now().strftime("%Y/%m")  #datetime.datetime.today().strftime("%Y/%m")
    date = datetime.today().strftime("%d.%m.%Y")
    filename = f"/receipts/{year_month}/{student_name}_{fee_type.replace(' ', '_')}_{date}.pdf"
    
    # Save to file
    c.save()
    #with open(pdf_path, "wb") as f:
    #    f.write(buffer.getvalue())

    buffer.seek(0)
    # Upload to Dropbox
    dropbox_filename = filename
    dropbox_link = upload_to_dropbox(buffer, dropbox_filename)
    return buffer,dropbox_link  

# User Authentication Function
def login():
    st.title("🔐 Login to Receipt Generator")
    
    username = st.text_input("Username", "")
    password = st.text_input("Password", "", type="password")
    
    if st.button("Login"):
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid Username or Password")

def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        login()
        return

    st.title("🧾Receipt Generator")
    
    receipt_number = datetime.now().strftime("%Y%m%d%H%M") 
    student_name = st.text_input("Student Name", "")
    date = datetime.today().strftime("%d/%m/%Y")
    amount_paid = st.number_input("Amount Paid", min_value=0.0, value=0.0)
    
    fee_type = st.selectbox("Type of Fees", ["Tuition Fee", "Admission Fee"])
    month = ""
    if fee_type == "Tuition Fee":
        month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
    
    logo_path = "logo-bg-removed.png"
    
    if st.button("Generate Receipt"):
        if student_name and amount_paid > 0:
            data = {
                "Receipt Number": receipt_number,
                "Student Name": student_name,
                "Date": date,
                "Amount Paid": amount_paid,
                "Fee Type": fee_type,
                "Month": month if fee_type == "Tuition Fee" else ""
            }
            save_to_csv(data)
            pdf_buffer,dropbox_link  = generate_receipt(receipt_number, student_name, date, amount_paid, fee_type, month, logo_path)
            if dropbox_link:
                st.success("Receipt generated successfully!")
                st.markdown(f"[Download from Dropbox]({dropbox_link})")
            else:
                st.error("Failed to upload receipt to Dropbox.")
            
            st.download_button("Download Receipt", pdf_buffer, file_name=f"{student_name}_{fee_type}_{date}.pdf", mime="application/pdf")
        else:
            st.error("Please fill all required fields.")

if __name__ == "__main__":
    main()
