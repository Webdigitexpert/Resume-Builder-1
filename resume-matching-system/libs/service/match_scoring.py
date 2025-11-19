from sentence_transformers import util

def calculate_similarity_score(resume_embedding, jd_embedding):
    score = util.cos_sim(resume_embedding, jd_embedding)
    return float(score[0][0] * 100)

def skill_gap_analysis(resume_skills, jd_skills):
    missing = list(set(jd_skills) - set(resume_skills))
    matched = list(set(jd_skills) & set(resume_skills))
    return matched, missing
