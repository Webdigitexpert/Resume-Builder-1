import re
from libs.service.resume_parser import extract_skills

def extract_resume_details(text: str):
    # --------- Extract Email ---------
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    email = email_match.group(0) if email_match else None

    # --------- Extract Phone ---------
    phone_match = re.search(r"\+?\d[\d\s\-]{8,15}", text)
    phone = phone_match.group(0).strip() if phone_match else None

    # --------- Extract Name (first line heuristic) ---------
    lines = text.split("\n")
    name = lines[0].strip() if len(lines[0]) < 50 else None

    # --------- Extract Experience (years) ---------
    exp_match = re.search(
        r"(\d+)\s*(\+?\s*years?|yrs?|years of experience)",
        text.lower(),
    )
    experience = int(exp_match.group(1)) if exp_match else 0

    # --------- Extract Skills ---------
    skills = extract_skills(text)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "experience": experience,
        "skills": skills,
    }
