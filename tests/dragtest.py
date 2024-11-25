

# Example usage:
markdown_content = "# md-to-pdf\n\nA web service for converting markdown to PDF"
pdf_content = convert_md_to_pdf(markdown_content)
with open('output.pdf', 'wb') as f:
    f.write(pdf_content)
