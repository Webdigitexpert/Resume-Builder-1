from reportlab.pdfgen import canvas

def export_score_pdf(path, score, matched, missing):
    c = canvas.Canvas(path)
    c.drawString(100, 800, f"Job Match Score: {score}")
    c.drawString(100, 760, f"Matched Skills: {', '.join(matched)}")
    c.drawString(100, 720, f"Missing Skills: {', '.join(missing)}")
    c.save()
