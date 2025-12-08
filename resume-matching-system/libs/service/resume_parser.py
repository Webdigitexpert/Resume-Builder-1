import re
from datetime import datetime
from dateutil import parser


########################################
# TEXT EXTRACTION
########################################

def extract_text_from_pdf(path: str) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(path)
    pages = []
    for p in reader.pages:
        try:
            txt = p.extract_text()
            if txt:
                pages.append(txt)
        except:
            pass
    return "\n".join(pages)


def extract_text_from_docx(path: str) -> str:
    import docx2txt
    return docx2txt.process(path) or ""


def extract_text_from_image(path: str) -> str:
    import pytesseract
    from PIL import Image
    return pytesseract.image_to_string(Image.open(path)) or ""


def parse_resume_to_text(file_path: str) -> str:
    fp = file_path.lower()
    if fp.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif fp.endswith(".docx"):
        return extract_text_from_docx(file_path)
    else:
        return extract_text_from_image(file_path)


########################################
# BASIC FIELDS — EMAIL, PHONE, NAME
########################################

def extract_email(text: str) -> str | None:
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return m.group(0) if m else None


def extract_phone(text: str) -> str | None:
    m = re.search(r"(\+?\d[\d\s\-()]{7,})", text)
    if not m:
        return None
    ph = re.sub(r"\s+", " ", m.group(1)).strip()
    return ph


def extract_name(text: str) -> str | None:
    """
    Extracts candidate name even when first and last names are split across lines,
    like:
        Jiaming
        Chen
    Or when combined on one line.
    """

    lines = [l.strip() for l in text.splitlines()]
    lines = [l for l in lines if l and l not in ["|", "-"]]

    # Remove lines containing contact info
    contact_keywords = ["@", "linkedin", "github", "phone", "www", ".com", "(", ")"]
    clean_lines = []
    for ln in lines:
        if any(k in ln.lower() for k in contact_keywords):
            continue
        clean_lines.append(ln)

    # Try normal name extraction (single line)
    for ln in clean_lines[:5]:
        if re.match(r"^[A-Za-z][A-Za-z\s\-]{1,40}$", ln):
            parts = ln.split()
            if 1 < len(parts) <= 4:
                return " ".join(p.capitalize() for p in parts)

    # If name is split across multiple lines (your case)
    first_two = clean_lines[:2]

    if (len(first_two) == 2 and
        re.match(r"^[A-Za-z\-]+$", first_two[0]) and
        re.match(r"^[A-Za-z\-]+$", first_two[1])):
        return f"{first_two[0].capitalize()} {first_two[1].capitalize()}"

    return None



########################################
# EXPERIENCE — ACCURATE WORK EXPERIENCE ONLY
########################################

def extract_work_section(text: str) -> str:
    """
    Extract the WORK EXPERIENCE block so other dates (education/projects) don't pollute the result.
    """
    match = re.search(
        r"(WORK EXPERIENCE|EXPERIENCE)(.*?)(PROJECTS|EDUCATION|SKILLS|CERTIFICATIONS|SUMMARY)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group(2)

    return text  # fallback


def extract_experience_years(text: str) -> dict:
    text = text.lower()
    total_months = 0

    #########################
    # 1. EXPLICIT "4 months", "10 mos", "2 years"
    #########################
    for val, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(month|months|mos)", text):
        total_months += float(val)

    for val, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(year|years|yr|yrs)", text):
        total_months += float(val) * 12

    #########################
    # 2. DATE RANGES: Jun 2022 – Sep 2022, 2021 – Present
    #########################
    date_ranges = re.findall(
        r"([A-Za-z]{3,9}\s*\d{4})\s*[-–]\s*(Present|Current|[A-Za-z]{3,9}\s*\d{4})",
        text,
        re.IGNORECASE,
    )

    for start, end in date_ranges:
        try:
            start_dt = parser.parse(start)
            end_dt = datetime.now() if "present" in end.lower() else parser.parse(end)

            months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
            if months > 0:
                total_months += months
        except:
            pass

    #########################
    # FINAL OUTPUT
    #########################
    return {
        "months": int(total_months),
        "years": round(total_months / 12, 2),
    }


########################################
# SKILLS CATEGORIZATION
########################################

def extract_skills(text: str) -> dict:
    text = text.lower()

    programming_languages = [
        "python", "java", "c", "c++", "c#", "javascript", "typescript",
        "go", "rust", "kotlin", "swift", "ruby", "php", "r", "matlab"
    ]

    frontend = [
        "html", "css", "javascript", "typescript",
        "react", "reactjs", "next.js", "nextjs", "angular",
        "vue", "vuejs", "jquery", "bootstrap", "tailwind", "chart.js"
    ]

    backend = [
        "nodejs", "node.js", "express", "django", "flask",
        "spring", "spring boot", "fastapi", "laravel"
    ]

    databases = [
        "mysql", "postgresql", "postgres", "mongodb",
        "redis", "sqlite", "oracle", "sql server"
    ]

    cloud_devops = [
        "docker", "kubernetes", "k8s", "aws", "azure", "gcp",
        "jenkins", "github actions", "gitlab ci",
        "terraform", "linux", "windows", "macos"
    ]

    ml_ai = [
        "pandas", "numpy", "scikit-learn", "sklearn",
        "scipy", "machine learning", "deep learning",
        "pytorch", "tensorflow", "nlp", "computer vision"
    ]

    tools = [
        "git", "github", "gitlab", "jira", "confluence",
        "swagger", "docker compose"
    ]

    def match(category):
        found = []
        for s in category:
            if re.search(r"\b" + re.escape(s.lower()) + r"\b", text):
                found.append(s)
        return found

    return {
        "programming_languages": match(programming_languages),
        "frontend": match(frontend),
        "backend": match(backend),
        "databases": match(databases),
        "cloud_devops": match(cloud_devops),
        "ml_ai": match(ml_ai),
        "tools": match(tools),
        "others": [],
    }


########################################
# MASTER FUNCTION
########################################

def extract_details(text: str) -> dict:
    work_text = extract_work_section(text)
    exp = extract_experience_years(work_text)

    print("\n===== DEBUG: FIRST 20 LINES OF RESUME TEXT =====")
    for i, line in enumerate(text.splitlines()[:20]):
        print(i, repr(line))
    print("================================================\n")

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "experience": {
            "years": exp["years"],
            "months": exp["months"]
        },
        "skills": extract_skills(text),
    }

