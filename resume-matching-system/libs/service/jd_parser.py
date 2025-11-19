def parse_job_description(text: str):
    lines = text.lower().splitlines()
    required_skills = []
    experience = None

    for line in lines:
        if "experience" in line:
            experience = line
        if "skills" in line or "requirements" in line:
            required_skills.extend(line.split(","))

    return {
        "skills_required": [s.strip() for s in required_skills],
        "experience_required": experience
    }
