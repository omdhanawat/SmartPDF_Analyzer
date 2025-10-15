import fitz, re, time, numpy as np
from pathlib import Path

try:
    from gensim_shim import summarization
    summarize = summarization.summarize
except Exception:
    summarize = None


class RuleEngine:
    """Adaptive rule engine for intelligent section splitting."""
    def __init__(self):
        self.rules = {
            "heading_word_limit": 12,
            "semantic_gap_threshold": 1.8,
        }

    def adapt_rules(self, lines):
        line_lengths = [len(line.split()) for line in lines if line.strip()]
        if not line_lengths:
            return
        avg_len = np.mean(line_lengths)
        std_len = np.std(line_lengths)

        self.rules["heading_word_limit"] = int(min(max(6, 0.9 * avg_len), 15))
        self.rules["semantic_gap_threshold"] = 1.5 + (std_len / (avg_len + 1e-5))

    def is_heading(self, line):
        line = line.strip()
        if not line:
            return False

        # Heuristic pattern detection
        if len(line.split()) <= self.rules["heading_word_limit"]:
            if line.isupper() or line.istitle() or re.match(r"^[A-Z][A-Za-z0-9\s,:;’'\"&\-()]+$", line):
                return True

        # Common heading triggers
        heading_keywords = [
            "introduction", "overview", "summary", "conclusion",
            "chapter", "section", "objective", "purpose", "background", "recipe"
        ]
        if any(k in line.lower() for k in heading_keywords):
            return True

        return False


class PDFProcessor:
    """Extracts, sections, and summarizes PDFs dynamically."""
    def __init__(self, persona=None, job=None):
        self.persona = persona or "General User"
        self.job = job or "Document analysis"
        self.rules = RuleEngine()

    def process_pdf(self, pdf_path):
        start = time.time()
        doc = fitz.open(pdf_path)
        all_lines, full_text = [], ""

        for page in doc:
            page_text = page.get_text("text")
            lines = [l.strip() for l in page_text.split("\n") if l.strip()]
            all_lines.extend(lines)
            full_text += page_text + "\n"
        doc.close()

        self.rules.adapt_rules(all_lines)
        sections = self._split_into_sections(all_lines)
        results = []

        for s in sections:
            summary = self._summarize(s["content"])
            results.append({"section_title": s["title"], "summary": summary})

        return {"sections": results, "processing_time": round(time.time() - start, 3)}

    def _split_into_sections(self, lines):
        sections, buffer, current_title = [], [], "General"

        for line in lines:
            if self.rules.is_heading(line) and len(buffer) > 8:
                joined = " ".join(buffer).strip()
                if joined:
                    sections.append({"title": current_title, "content": joined})
                buffer, current_title = [], line
            else:
                buffer.append(line)

        if buffer:
            sections.append({"title": current_title, "content": " ".join(buffer)})
        return sections

    def _summarize(self, text, max_sents=3):
        text = re.sub(r"\s+", " ", text.strip())
        if len(text.split()) < 60:
            return text
        try:
            if summarize:
                word_count = len(text.split())
                ratio = 0.08 if word_count > 800 else 0.15
                s = summarize(text, ratio=ratio)
                if s:
                    return f"For a {self.persona} working to {self.job}, key points: " + s
        except Exception:
            pass
        sents = re.split(r"(?<=[.!?])\s+", text)
        return " ".join(sents[:max_sents]).strip()
