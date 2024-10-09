# converter/views.py
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import os
import language_tool_python
from docx import Document
import pdfplumber  # Make sure to install this library
import re
def capitalize_after_full_stop(text):
    return re.sub(r'([.!?])\s*(\w)', lambda x: x.group(1) + ' ' + x.group(2).upper(), text)



def upload_file(request):
    grammar_issues = []
    if request.method == 'POST' and request.FILES['pdf_file']:
        pdf_file = request.FILES['pdf_file']
        fs = FileSystemStorage()
        filename = fs.save(pdf_file.name, pdf_file)
        file_path = fs.url(filename)

        # Extract text from PDF
        text = ""
        try:
            with pdfplumber.open(os.path.join('media', filename)) as pdf:
                text = '\n'.join(page.extract_text() for page in pdf.pages if page.extract_text())
            print(f"Extracted text from PDF: {text}")
        except Exception as e:
            print(f"Error during PDF text extraction: {str(e)}")
            return render(request, 'upload.html', {
                'error': f"Error during PDF text extraction: {str(e)}"
            })

        # Check grammar
        tool = language_tool_python.LanguageTool('en-US')
        grammar_issues = tool.check(text)

        # Print error words and suggestions
        for issue in grammar_issues:
            error_word = issue.context.text if hasattr(issue, 'context') and hasattr(issue.context,
                                                                                     'text') else "Unknown"
            suggestions = ', '.join(issue.replacements) if issue.replacements else "No suggestions"
            print(f"Error: '{error_word}' | Suggestions: {suggestions}")

        # Apply corrections to the text
        corrected_text = tool.correct(text)

        corrected_text = capitalize_after_full_stop(corrected_text)

        # Save corrected text to a DOCX file
        corrected_docx_filename = 'corrected_' + filename.replace('.pdf', '.docx')
        corrected_docx_path = os.path.join('media', corrected_docx_filename)
        corrected_doc = Document()
        corrected_doc.add_paragraph(corrected_text)
        corrected_doc.save(corrected_docx_path)
        print(f"Saved corrected document to {corrected_docx_path}")

        return render(request, 'upload.html', {
            'file_path': file_path,
            'corrected_docx_path': f'/media/{corrected_docx_filename}',  # Return the correct path
            'grammar_issues': grammar_issues,
            'text':text,
            'correct_text':corrected_text,
        })

    return render(request, 'upload.html')