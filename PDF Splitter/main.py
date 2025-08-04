import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PyPDF2 import PdfReader, PdfWriter

class PDFSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Splitter")
        self.pdf_path = None

        self.label = tk.Label(root, text="No PDF selected")
        self.label.pack(pady=10)

        self.select_button = tk.Button(root, text="Select PDF", command=self.select_pdf)
        self.select_button.pack(pady=5)

        self.split_button = tk.Button(root, text="Split PDF", command=self.split_pdf)
        self.split_button.pack(pady=5)

    def select_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.pdf_path = file_path
            self.label.config(text=f"Selected: {os.path.basename(file_path)}")

    def split_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("No File", "Please select a PDF file first.")
            return

        try:
            reader = PdfReader(self.pdf_path)
            output_dir = os.path.splitext(self.pdf_path)[0] + "_pages"
            os.makedirs(output_dir, exist_ok=True)

            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                output_path = os.path.join(output_dir, f"page_{i+1}.pdf")
                with open(output_path, "wb") as f:
                    writer.write(f)

            messagebox.showinfo("Success", f"PDF split into {len(reader.pages)} pages.\nSaved in: {output_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to split PDF:\n{e}")

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFSplitterApp(root)
    root.mainloop()
