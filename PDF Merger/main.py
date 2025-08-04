import PyPDF2

def merge_first_page(pdf1, pdf2, output_path):
    pdf_merger = PyPDF2.PdfMerger()

    # Read the first page of the first PDF
    with open(pdf1, 'rb') as file1:
        reader1 = PyPDF2.PdfReader(file1)
        first_page = reader1.pages[0]

        # Create a temporary PDF with the first page
        temp_pdf = PyPDF2.PdfWriter()
        temp_pdf.add_page(first_page)

        # Write the temporary PDF to a file
        with open('temp_first_page.pdf', 'wb') as temp_file:
            temp_pdf.write(temp_file)

    # Append the temporary PDF with the first page
    pdf_merger.append('temp_first_page.pdf')

    # Append the entire second PDF
    pdf_merger.append(pdf2)

    # Write the merged PDF to the output file
    with open(output_path, 'wb') as output_file:
        pdf_merger.write(output_file)

# Paths to the PDF files
pdf1 = '1.1.pdf'
pdf2 = '2.1.pdf'
output_file = '402420412 - Mathematics 511.pdf'

merge_first_page(pdf1, pdf2, output_file)
