import docx2txt
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
import re

def extract_text_from_pdf(path):
    reader = PdfReader(path)
    return "\n".join([page.extract_text() for page in reader.pages])

def extract_text_from_docx(path):
    return docx2txt.process(path)

def extract_text_from_image(path):
    return pytesseract.image_to_string(Image.open(path))

def parse_resume_to_text(file_path: str):
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)
    else:
        return extract_text_from_image(file_path)

def extract_skills(text: str):
    skill_keywords = ["python", "fastapi", "docker", "aws", "ml", "nlp", "react"]
    return [skill for skill in skill_keywords if skill.lower() in text.lower()]
