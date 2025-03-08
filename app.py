import streamlit as st
import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch credentials from environment variables
VALID_USERNAME = os.getenv("APP_USERNAME")
VALID_PASSWORD = os.getenv("APP_PASSWORD")

# CSV File for storing records
data_file = "receipts.csv"

def save_to_csv(data):
    df = pd.DataFrame([data])
    if not os.path.exists(data_file):
        df.to_csv(data_file, index=False)
    else:
        df.to_csv(data_file, mode='a', header=False, index=False)

def generate_receipt(receipt_number, student_name, date, amount_paid, fee_type, month):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(230, height - 50, "RECEIPT")
    c.setFont("Helvetica", 12)
    c.drawString(400, height - 80, f"Receipt #: {receipt_number}")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 120, "FROM")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 140, "Nucleon Kota Shantiniketan")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 200, f"BILL TO - {student_name}")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 230, "DATE")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 245, date)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, height - 230, "BALANCE PAID")
    c.setFont("Helvetica", 15)
    c.drawString(400, height - 245, f"₹ {amount_paid:.2f}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 280, "DESCRIPTION")
    c.drawString(450, height - 280, "TOTAL")

    c.setFont("Helvetica", 10)
    description = fee_type if fee_type == "Admission Fee" else f"Tuition Fees: ({month})"
    c.drawString(50, height - 300, description)
    c.drawString(450, height - 300, f"₹ {amount_paid:.2f}")
    
    c.setFont("Helvetica", 70)
    c.setFillAlpha(0.1)
    c.drawString(130, height / 2, "Nucleon Kota")
    
    # Save PDF in memory
    c.save()
    buffer.seek(0)
    return buffer

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

# Main App
def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        login()
        return
    
    st.title("🧾 Receipt Generator")
    
    receipt_number = datetime.now().strftime("%Y%m%d%H%M")
    student_name = st.text_input("Student Name", "")
    date = datetime.today().strftime("%d/%m/%Y")
    amount_paid = st.number_input("Amount Paid", min_value=0.0, value=0.0)
    
    fee_type = st.selectbox("Type of Fees", ["Tuition Fee", "Admission Fee"])
    month = ""
    if fee_type == "Tuition Fee":
        month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
    
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
            pdf_buffer = generate_receipt(receipt_number, student_name, date, amount_paid, fee_type, month)
            st.download_button("Download Receipt", pdf_buffer, file_name=f"{student_name}_{fee_type}_{date}.pdf", mime="application/pdf")
        else:
            st.error("Please fill all required fields.")

    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.experimental_rerun()

if __name__ == "__main__":
    main()
