from PyPDF2 import PdfReader
import os
import docx2txt


class FileConverter:
    @staticmethod
    def convert_to_text(file_path: str) -> str:
        """Convert PDF or DOCX files to plain text."""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return FileConverter._pdf_to_text(file_path)
        elif file_extension in ['.docx', '.doc']:
            return FileConverter._docx_to_text(file_path)
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    @staticmethod
    def _pdf_to_text(pdf_path: str) -> str:
        """Extract text from PDF file."""
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def _docx_to_text(docx_path: str) -> str:
        """Extract text from DOCX file using docx2txt."""
        text = docx2txt.process(docx_path)
        return text