import customtkinter as ctk
from tkinter import filedialog, messagebox
import pdfplumber
import pandas as pd
import re
import os
import logging
import shutil
from datetime import datetime
import zipfile

# Error Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Extract text from PDF files
def extract_text_from_pdf(file_path):
    text_list = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                text_list.append(text)
    except Exception as e:
        logging.error(f"Error extracting text from {file_path}: {e}")
    return text_list

#Add extracted text to dataframe
def pdf_to_dataframe(file_path):
    text_list = extract_text_from_pdf(file_path)
    df = pd.DataFrame(text_list, columns=["Text"])
    return df

def extract_info_and_save(file_paths, progress_label, summary_label):
    renamed_count = 0  # Counter for renamed files
    total_files = len(file_paths)  # Total number of files to be renamed
    not_renamed_files = []  # List to store files that were not renamed

    company_prefixes = {
        "CNC": "Cancam",
        "CA": "Cancam",
        "WA": "Wavelengths",
        "NE": "Nexgistix",
        "IN": "Advance",
        "JU": "Jumaras",
        "ZI": "Copperzone",
        "HL": "Headland",
        "IC": "Headland",
        "VE": "Vectura"
    }


    client_patterns = {
        "CMOC": r"CMOC\s*-\s*MANIFEST\s*\d+|CMoC\s*-\s*Manifest\s*\d+|CMOC\s*-\s*Manifest\s*\d+",
        "4S Structures": r"4S\s*Structures\s*-\s*MANIFEST\s*\d+",
        "Breakdown": r"Breakdown\s*-\s*MANIFEST\s*\d+",
        "Polytra": r"Polytra\s*-\s*MANIFEST\s*\d+",
        "Sonorex": r"Sonorex\s*-\s*MANIFEST\s*\d+",
        "IXM": r"IXM\s*-\s*MANIFEST\s*\d+",
        "TFM": r"TFM\s*-\s*MANIFEST\s*\d+",
        "Tricore": r"Tricore\s*-\s*MANIFEST\s*\d+",
        "ATT": r"ATT\s*-\s*MANIFEST\s*\d+",
        "Cash Sales": r"Cash\s*Sales\s*-\s*MANIFEST\s*\d+",
        "KML": r"KML\s*-\s*MANIFEST\s*\d+",
        "KFM": r"KFM\s*-\s*MANIFEST\s*\d+|KFM\s*-\s*Manifest\s*\d+|KFM\s*-\s*Manifest\s*\d+",
        "Loanstock": r"Loanstock\s*-\s*MANIFEST\s*\d+",
        "Matvin": r"Matvin\s*-\s*MANIFEST\s*\d+",
        "Reload": r"Reload\s*-\s*MANIFEST\s*\d+",
        "Venditime Zambia": r"Venditime\s*Zambia\s*-\s*MANIFEST\s*\d+",
        "BRAKE LINING": r"BRAKE\s*LINING\s*\d+",
        "BRITALMIN": r"BRITALMIN\s*-\s*\d+",
        "ATT": r"ATT\s*\d+",
        "VT": r"VT\s*\d+",
    }

    renamed_files_info = []  # List to store original and new names of renamed files
    renamed_counts = {client: 0 for client in client_patterns.keys()}  # Counter for each client

    # Create 'Invoices' folder on the desktop
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    invoices_folder_path = os.path.join(desktop_path, 'Invoices')
    if not os.path.exists(invoices_folder_path):
        os.makedirs(invoices_folder_path)

    for file_path in file_paths:
        try:
            # Convert PDF to DataFrame
            df = pdf_to_dataframe(file_path)
            # Extract invoice number
            prefix_match = None
            for prefix in company_prefixes.keys():
                prefix_pattern = rf"\b{prefix}\d{{6}}\b"
                prefix_match = re.search(prefix_pattern, df['Text'].str.cat(sep=' '))
                if prefix_match:
                    company_prefix = prefix
                    break

            if not prefix_match:
                logging.info(f"Company prefix not found in the PDF: {file_path}")
                not_renamed_files.append((file_path, "Company prefix not found"))
                continue

            invoice_number = prefix_match.group(0)

            client_match = None
            for client, pattern in client_patterns.items():
                client_match = re.search(pattern, df['Text'].str.cat(sep=' '), re.IGNORECASE)
                if client_match:
                    client_string = client_match.group(0)
                    break

            if not client_match:
                logging.error(f"Could not find the client string in the PDF: {file_path}")
                not_renamed_files.append((file_path, f"Client string not found"))
                continue

            # Extract only the "MANIFEST 123456" part from the client string
            manifest_match = re.search(r"MANIFEST\s*\d+", client_string)
            if manifest_match:
                manifest_string = manifest_match.group(0)
            else:
                logging.error(f"Could not extract manifest string from client string in the PDF: {file_path}")
                not_renamed_files.append((file_path, f"Manifest string not found"))
                continue

            # Save the renamed PDF to the 'Invoices' folder in the appropriate company folder
            company_folder_path = os.path.join(invoices_folder_path, company_prefixes[company_prefix] + " Invoices")
            if not os.path.exists(company_folder_path):
                os.makedirs(company_folder_path)

            new_file_name = f"{client} - {company_prefixes[company_prefix]} - {invoice_number} - {manifest_string}.pdf"
            new_file_path = os.path.join(company_folder_path, new_file_name)

            with open(file_path, "rb") as original_pdf:
                with open(new_file_path, "wb") as new_pdf:
                    new_pdf.write(original_pdf.read())

            logging.info(f"PDF saved as: {new_file_path}")
            renamed_count += 1
            renamed_counts[client] += 1

            # Store original and new names of renamed files
            renamed_files_info.append((os.path.basename(file_path), new_file_name))

            # Update progress label
            progress_label.configure(text=f"{renamed_count} of {total_files} files renamed")
            root.update_idletasks()

        except Exception as e:
            logging.error(f"An error occurred with file {file_path}: {e}")
            not_renamed_files.append((file_path, str(e)))

    # Move original PDFs to 'Original Invoices' folder inside 'Invoices' folder and create a zip archive
    original_invoices_folder_path = os.path.join(invoices_folder_path, 'Original Invoices')
    if not os.path.exists(original_invoices_folder_path):
        os.makedirs(original_invoices_folder_path)

    for file_path in file_paths:
        shutil.move(file_path, original_invoices_folder_path)

    # Create a zip archive of the 'Original Invoices' folder
    archive_name = f"Archive - {datetime.now().strftime('%Y-%m-%d')}.zip"
    archive_path = os.path.join(invoices_folder_path, archive_name)
    shutil.make_archive(os.path.splitext(archive_path)[0], 'zip', original_invoices_folder_path)

    # Generate summary text document in the original folder and move it to the archive folder
    summary_file_path = os.path.join(original_invoices_folder_path, 'renaming_summary.txt')
    with open(summary_file_path, 'w') as summary_file:
        summary_file.write("Renaming Summary\n")
        summary_file.write("================\n\n")
        summary_file.write("Renamed Files:\n")
        for original_name, new_name in renamed_files_info:
            summary_file.write(f"{original_name} -> {new_name}\n")
        
        summary_file.write("\nNot Renamed Files:\n")
        for file_path, reason in not_renamed_files:
            summary_file.write(f"{os.path.basename(file_path)}: {reason}\n")

    # Add the summary file to the archive
    with zipfile.ZipFile(archive_path, 'a') as archive:
        archive.write(summary_file_path, os.path.basename(summary_file_path))

    # Delete the 'Original Invoices' folder after creating the archive
    shutil.rmtree(original_invoices_folder_path)

    # Show the total number of files renamed and clear progress label after user clicks OK
    messagebox.showinfo("Summary", f"Total number of files renamed: {renamed_count}")
    progress_label.configure(text="")
    logging.info(f"Total number of files renamed: {renamed_count}")

    # Update summary label in the UI
    summary_text = "Renaming Summary\n\n"
    for client, count in renamed_counts.items():
        if count > 0:
            summary_text += f"{client}: {count} renamed\n"
    summary_label.configure(text=summary_text)

def process_pdfs(progress_label):
    # Open file dialog to select the folder containing PDF files
    folder_path = filedialog.askdirectory()
    if not folder_path:
        return None
    # Get all PDF files in the selected folder
    file_paths = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.lower().endswith('.pdf')]

    return file_paths

def rename_and_save_files(file_paths, progress_label, summary_label):
    extract_info_and_save(file_paths, progress_label, summary_label)

# Create the main customtkinter window
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("Doby!")
root.geometry("270x340")

# Set the icon of the application
root.iconbitmap('doby.png')

# Initialize variables to store file paths
file_paths = []

# Add an Upload Files button to trigger the operation for selecting files
def upload_files():
    global file_paths
    file_paths = process_pdfs(progress_label)
    if file_paths:
        files_found_label.configure(text=f"Files Found: {len(file_paths)}")
        files_found_label.place(relx=0.5, rely=0.9, anchor='s')
        progress_label.configure(text="")  # Clear the progress label

upload_button = ctk.CTkButton(root, text="Upload Files", command=upload_files)
upload_button.pack(pady=10)

# Add a label to show the number of files found underneath the GO button
files_found_label = ctk.CTkLabel(root, text="", text_color="light grey", font=("Arial", 12))
files_found_label.place_forget()

# Add a label to show progress at the bottom center portion of the UI
progress_label = ctk.CTkLabel(root, text="", text_color="light grey", font=("Arial", 12))
progress_label.place(relx=0.5, rely=1.0, anchor='s')

# Add a label to show the summary of the renaming process
summary_label = ctk.CTkLabel(root, text="", text_color="light grey", font=("Arial", 12))
summary_label.pack(pady=10)

# Add a GO! button to trigger renaming and saving files
def go_button_click():
    rename_and_save_files(file_paths, progress_label, summary_label)
    files_found_label.place(relx=0.5, rely=0.95, anchor='s')

go_button = ctk.CTkButton(root, text="GO!", command=go_button_click)
go_button.pack(pady=10)

# Run the customtkinter event loop
root.mainloop()