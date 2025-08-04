import tkinter
import customtkinter
from tkinter import filedialog
import os
import re
import shutil
import pypdfium2 as pdfium
from datetime import datetime

class PDFRenamerApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("PDF Invoice Renamer")
        self.geometry("700x600") # Adjusted height as dropdown is removed

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")

        self.pdf_files_to_rename = []
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.base_renamed_invoices_dir = os.path.join(self.desktop_path, "Renamed Invoices") # Base directory for all output
        self.successfully_renamed_dir = self.base_renamed_invoices_dir # Renamed files go here
        self.not_renamed_dir = os.path.join(self.base_renamed_invoices_dir, "Not Renamed") # Skipped files go here

        # Company abbreviations from user's code
        self.company_abbreviations = {
            "COPPERZONE LOGISTICS LIMITED": "CZZ",
            "HEADLAND LOGISTICS LIMITED": "HDL",
            "VECTURA LOGISTICS LIMITED": "VL",
            "JUMARAS LIMITED": "JL",
            "ADVANCE TRANSPORT LIMITED": "ADV",
            "NEXGISTIX TRANSPORT LIMITED": "NX",
            "WAVELENGTHS TRANSPORT LIMITED": "WL",
            "CANCAM TRANSPORT LIMITED": "CCL"
        }
        if self.company_abbreviations:
            self.known_senders_pattern = r"(" + "|".join(re.escape(name) for name in self.company_abbreviations.keys()) + r")"
        else:
            self.known_senders_pattern = r""

        # --- UI Elements ---
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.select_folder_button = customtkinter.CTkButton(self.main_frame, text="Select Folder with Invoices", command=self.select_folder)
        self.select_folder_button.pack(pady=10)

        self.select_files_button = customtkinter.CTkButton(self.main_frame, text="Select Invoice Files", command=self.select_files)
        self.select_files_button.pack(pady=10)

        self.files_found_label = customtkinter.CTkLabel(self.main_frame, text="PDFs selected: 0")
        self.files_found_label.pack(pady=10)

        self.rename_button = customtkinter.CTkButton(self.main_frame, text="Rename Selected PDFs", command=self.rename_pdfs, state="disabled")
        self.rename_button.pack(pady=20)

        self.log_textbox = customtkinter.CTkTextbox(self.main_frame, height=300, state="disabled") # Increased height
        self.log_textbox.pack(pady=10, padx=10, fill="both", expand=True)

    def log_message(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert(tkinter.END, message + "\n")
        self.log_textbox.see(tkinter.END)
        self.log_textbox.configure(state="disabled")
        self.update_idletasks()

    def select_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder Containing PDF Invoices")
        if folder_path:
            self.pdf_files_to_rename = []
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(".pdf"):
                    self.pdf_files_to_rename.append(os.path.join(folder_path, filename))
            self.update_files_found_label()
            self.log_message(f"Selected folder: {folder_path}")
            self.log_message(f"Found {len(self.pdf_files_to_rename)} PDF files.")

    def select_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select PDF Invoice Files",
            filetypes=(("PDF files", "*.pdf"), ("All files", "*.*"))
        )
        if file_paths:
            self.pdf_files_to_rename = list(file_paths)
            self.update_files_found_label()
            self.log_message(f"Selected {len(self.pdf_files_to_rename)} PDF files.")

    def update_files_found_label(self):
        count = len(self.pdf_files_to_rename)
        self.files_found_label.configure(text=f"PDFs selected: {count}")
        if count > 0:
            self.rename_button.configure(state="normal")
        else:
            self.rename_button.configure(state="disabled")

    def extract_text_from_pdf(self, pdf_path):
        text_content = ""
        try:
            pdf_doc = pdfium.PdfDocument(pdf_path)
            for i in range(len(pdf_doc)):
                page = pdf_doc.get_page(i)
                textpage = page.get_textpage()
                text_content += textpage.get_text_range() + "\n"
                textpage.close()
                page.close()
            pdf_doc.close()
        except Exception as e:
            self.log_message(f"Error reading PDF {os.path.basename(pdf_path)}: {e}")
            return None
        return text_content

    def extract_invoice_data_for_rename(self, pdf_text, pdf_name):
        data = {}
        
        # 1. Extract Company Code (Sender's Company Abbreviation)
        company_code = None
        if self.known_senders_pattern:
            match = re.search(self.known_senders_pattern, pdf_text, re.IGNORECASE)
            if match:
                found_name_in_pdf = match.group(1)
                extracted_full_company_name = None
                for key_from_dict in self.company_abbreviations.keys():
                    if key_from_dict.lower() == found_name_in_pdf.lower():
                        extracted_full_company_name = key_from_dict
                        break
                if extracted_full_company_name and extracted_full_company_name in self.company_abbreviations:
                    company_code = self.company_abbreviations[extracted_full_company_name]
                    data["company_code"] = company_code
                else:
                    self.log_message(f"Found text '{found_name_in_pdf}' but could not map to a defined company abbreviation for {pdf_name}.")
                    return None # Indicates failure to extract this part
            else:
                self.log_message(f"Could not find a known sender company name in {pdf_name}.")
                return None
        else:
            self.log_message(f"Company abbreviation map is empty. Cannot determine company code for {pdf_name}.")
            return None

        # 2. Auto-detect Client and Extract Manifest Number
        client_for_naming = None
        manifest_num = None
        client_manifest_patterns = {
            "CMOC": r"CMOC - MANIFEST\s*(\d+)",
            "TFM": r"TFM - MANIFEST\s*(\d+)",
            "IXM": r"IXM - MANIFEST\s*(\d+)"
        }
        for client_name, pattern in client_manifest_patterns.items():
            manifest_num_match = re.search(pattern, pdf_text, re.IGNORECASE)
            if manifest_num_match:
                client_for_naming = client_name
                manifest_num = manifest_num_match.group(1)
                data["client_for_naming"] = client_for_naming
                data["manifest_num"] = manifest_num
                self.log_message(f"Detected client '{client_for_naming}' and Manifest No. '{manifest_num}' for {pdf_name}.")
                break
        if not client_for_naming:
            self.log_message(f"Could not detect a client (CMOC, TFM, or IXM) based on manifest patterns in {pdf_name}.")
            return None # Indicates failure to extract this part
        
        # 3. Extract Our Ref Num
        our_ref_num_match = re.search(r"Our Ref Num:\s*([A-Z0-9]+)", pdf_text, re.IGNORECASE)
        if our_ref_num_match:
            data["our_ref_num"] = our_ref_num_match.group(1)
        else:
            self.log_message(f"Could not find 'Our Ref Num:' in {pdf_name}.")
            return None # Indicates failure to extract this part
        
        return data

    def rename_pdfs(self):
        if not self.pdf_files_to_rename:
            self.log_message("No PDF files selected to rename.")
            return

        # Ensure base and subdirectories exist
        try:
            os.makedirs(self.successfully_renamed_dir, exist_ok=True) # For successfully renamed files
            os.makedirs(self.not_renamed_dir, exist_ok=True)      # For files that couldn't be renamed
            self.log_message(f"Ensured output directory exists: {self.base_renamed_invoices_dir}")
            self.log_message(f"Skipped files will be copied to: {self.not_renamed_dir}")
        except OSError as e:
            self.log_message(f"Error creating output directories: {e}")
            return
        
        renamed_count = 0
        skipped_count = 0
        successfully_renamed_summary = [] # For summary file
        skipped_files_summary = []      # For summary file

        for pdf_path in self.pdf_files_to_rename:
            original_pdf_name = os.path.basename(pdf_path)
            self.log_message(f"\nProcessing: {original_pdf_name}...")
            
            pdf_text = self.extract_text_from_pdf(pdf_path)
            reason_skipped = ""

            if not pdf_text:
                reason_skipped = "Error reading PDF content."
                # Fall through to invoice_data check
            
            invoice_data = None
            if pdf_text: # Only attempt to extract if PDF text was read
                invoice_data = self.extract_invoice_data_for_rename(pdf_text, original_pdf_name)
                if not invoice_data:
                    reason_skipped = "Could not extract all required data for renaming."
            
            if invoice_data: # If all data was extracted successfully
                try:
                    client_name_for_file = invoice_data['client_for_naming']
                    new_filename_base = (
                        f"{client_name_for_file} - " 
                        f"{invoice_data['company_code']} - "
                        f"{invoice_data['our_ref_num']} - "
                        f"MANIFEST {invoice_data['manifest_num']}"
                    )
                    
                    safe_filename_base = re.sub(r'[\\/*?:"<>|]', "_", new_filename_base)
                    new_filename_with_ext = f"{safe_filename_base}.pdf"
                    target_path_renamed = os.path.join(self.successfully_renamed_dir, new_filename_with_ext)

                    counter = 1
                    temp_filename_base_for_collision = safe_filename_base
                    while os.path.exists(target_path_renamed):
                        new_filename_with_ext = f"{temp_filename_base_for_collision}_{counter}.pdf"
                        target_path_renamed = os.path.join(self.successfully_renamed_dir, new_filename_with_ext)
                        counter += 1
                    
                    shutil.copy2(pdf_path, target_path_renamed) # Copy to successfully renamed folder
                    self.log_message(f"Successfully renamed (Client: {client_name_for_file}): {original_pdf_name} -> {new_filename_with_ext}")
                    successfully_renamed_summary.append(f"  Original: {original_pdf_name}\n  Renamed To: {new_filename_with_ext}\n  Detected Client: {client_name_for_file}\n")
                    renamed_count += 1
                except KeyError as e: # Should be less likely if extract_invoice_data_for_rename returns None on failure
                    reason_skipped = f"Missing data during filename construction (KeyError: {e})."
                    # Fall through to skip handling
                except Exception as e:
                    reason_skipped = f"Unexpected error during renaming: {e}."
                    # Fall through to skip handling
            
            # Handle skipping if invoice_data is None or an error occurred during renaming part
            if not invoice_data or reason_skipped:
                if not reason_skipped: # If reason_skipped was not set by a specific error above
                    reason_skipped = "Unknown reason for skipping (data extraction might have failed silently)."
                
                skipped_files_summary.append(f"  Original: {original_pdf_name}\n  Reason: {reason_skipped}\n")
                skipped_count += 1
                target_path_skipped = os.path.join(self.not_renamed_dir, original_pdf_name)
                try:
                    # Prevent overwriting if a file with the same name was already skipped
                    skip_counter = 1
                    base_name, ext = os.path.splitext(original_pdf_name)
                    temp_target_path_skipped = target_path_skipped
                    while os.path.exists(temp_target_path_skipped):
                        temp_target_path_skipped = os.path.join(self.not_renamed_dir, f"{base_name}_{skip_counter}{ext}")
                        skip_counter +=1
                    
                    shutil.copy2(pdf_path, temp_target_path_skipped)
                    self.log_message(f"Copied to 'Not Renamed' folder: {original_pdf_name} (as {os.path.basename(temp_target_path_skipped)})")
                except Exception as e_copy:
                    self.log_message(f"Error copying {original_pdf_name} to 'Not Renamed' folder: {e_copy}")
        
        self.log_message(f"\n--- Renaming Complete ---")
        self.log_message(f"Successfully renamed: {renamed_count} file(s).")
        self.log_message(f"Skipped (and copied to 'Not Renamed' folder): {skipped_count} file(s).")

        # Generate summary file with improved formatting
        if successfully_renamed_summary or skipped_files_summary:
            summary_filename = f"_Renaming_Summary_AutoDetected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            summary_filepath = os.path.join(self.base_renamed_invoices_dir, summary_filename) # Summary in the base "Renamed Invoices"
            try:
                with open(summary_filepath, "w") as f:
                    f.write("======================================================================\n")
                    f.write("          PDF Invoice Renaming Summary - Client Auto-Detection\n")
                    f.write(f"                          Run on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("======================================================================\n\n")

                    if skipped_files_summary:
                        f.write("----------------------------------------------------------------------\n")
                        f.write(f"FILES THAT COULD NOT BE RENAMED ({len(skipped_files_summary)}):\n")
                        f.write("(These files have been copied to the 'Not Renamed' subfolder)\n")
                        f.write("----------------------------------------------------------------------\n")
                        for detail in skipped_files_summary:
                            f.write(detail + "\n")
                        f.write("\n")
                    else:
                        f.write("----------------------------------------------------------------------\n")
                        f.write("All processed files were successfully renamed.\n")
                        f.write("----------------------------------------------------------------------\n\n")


                    if successfully_renamed_summary:
                        f.write("----------------------------------------------------------------------\n")
                        f.write(f"FILES SUCCESSFULLY RENAMED ({len(successfully_renamed_summary)}):\n")
                        f.write("----------------------------------------------------------------------\n")
                        for detail in successfully_renamed_summary:
                            f.write(detail + "\n")
                    else:
                        f.write("----------------------------------------------------------------------\n")
                        f.write("No files were successfully renamed in this run.\n")
                        f.write("----------------------------------------------------------------------\n\n")
                        
                    f.write("======================================================================\n")
                    f.write("End of Summary\n")
                    f.write("======================================================================\n")

                self.log_message(f"Renaming summary saved to: {summary_filepath}")
            except Exception as e:
                self.log_message(f"Error writing summary file: {e}")

if __name__ == "__main__":
    app = PDFRenamerApp()
    app.mainloop()
