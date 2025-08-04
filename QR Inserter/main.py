import qrcode
import fitz  # PyMuPDF
from io import BytesIO
from PIL import Image
import pandas as pd
import re

# Read the CSV file
csv_file = "urls.csv"
df = pd.read_csv(csv_file)

pdf_file = "Invoice1.pdf"
output_pdf = "AZ101999 INV0010020814 262.pdf"

# Open the original PDF
pdf_document = fitz.open(pdf_file)

# Generate QR Code
def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,  
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,  
        border=4
    )

    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image()
    img = img.resize((150, 150), Image.Resampling.LANCZOS)
    byte_io = BytesIO()
    img.save(byte_io, format='PNG')
    byte_io.seek(0)
    return byte_io

# Insert QR Code into PDF
def insert_qr_code_into_pdf(pdf_document, qr_code_stream, page_num):
    page = pdf_document.load_page(page_num)
    
    # Get the page dimensions (width and height)
    page_width = page.rect.width
    page_height = page.rect.height

    # Calculate the QR code position
    # Position from the left
    x0 = 28.35

    # Position from the bottom
    y1 = page_height - 140

    # Set the QR code width and height (e.g., 100x100 points)
    qr_width = 100
    qr_height = 100
    x1 = x0 + qr_width
    y0 = y1 - qr_height

    # Define the rectangle for the QR code
    rect = fitz.Rect(x0, y0, x1, y1)

    # Insert the QR code image into the page
    page.insert_image(rect, stream=qr_code_stream)

# Iterate through each page in the PDF
for page_num in range(len(pdf_document)):
    page = pdf_document.load_page(page_num)
    text = page.get_text()

    # Extract the invoice number using regex
    match = re.search(r"Our Ref Num:\s*(\w+)", text)
    if match:
        cisInvcNo = match.group(1)
        print(f"Found invoice number: {cisInvcNo} on page {page_num + 1}")

        # Find the corresponding QR code URL from the CSV
        qrCodeUrl = df.loc[df['cisInvcNo'] == cisInvcNo, 'qrCodeUrl'].values

        if qrCodeUrl.size > 0:
            qrCodeUrl = qrCodeUrl[0]
            # Generate QR code
            qr_code_stream = generate_qr_code(qrCodeUrl)

            # Insert QR code into PDF
            insert_qr_code_into_pdf(pdf_document, qr_code_stream, page_num)
        else:
            print(f"Warning: No QR code URL found for invoice number {cisInvcNo}")
    else:
        print(f"Warning: No invoice number found on page {page_num + 1}")

# Save the modified PDF
pdf_document.save(output_pdf)

print("QR codes have been inserted into the PDF successfully.")