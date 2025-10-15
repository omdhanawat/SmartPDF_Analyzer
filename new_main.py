import os, io, time, datetime
from pathlib import Path
from pdf_processor import PDFProcessor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


def export_pdf(report_text, output_path="SmartPDF_Report.pdf"):
    """Exports clean report to PDF."""
    styles = getSampleStyleSheet()
    story = []
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    for line in report_text.split("\n"):
        story.append(Paragraph(line.strip(), styles["Normal"]))
        story.append(Spacer(1, 6))
    doc.build(story)
    return output_path


def read_config(config_path):
    persona, job = None, None
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.lower().startswith("persona"):
                persona = line.split(":", 1)[1].strip()
            elif line.lower().startswith("job"):
                job = line.split(":", 1)[1].strip()
    return persona, job


def generate_report(input_folder="input", config_path="input_config.txt", output_file="final_output.txt"):
    persona, job = read_config(config_path)
    processor = PDFProcessor(persona, job)
    pdf_files = list(Path(input_folder).glob("*.pdf"))

    report = io.StringIO()
    report.write("SMARTPDF_ANALYZER REPORT\n")
    report.write("=" * 60 + "\n\n")
    report.write(f"Persona: {persona}\n")
    report.write(f"Job To Be Done: {job}\n")
    report.write(f"Input Documents: {', '.join([p.name for p in pdf_files])}\n")
    report.write(f"Processing Timestamp: {datetime.datetime.now().isoformat()}\n\n")
    report.write("=" * 70 + "\n\n")

    results, all_texts = [], []

    for pdf in pdf_files:
        print(f"Processing: {pdf.name} ...")
        try:
            res = processor.process_pdf(pdf)
            results.append((pdf.name, res, res["processing_time"]))
            all_texts.append(" ".join([s["summary"] for s in res["sections"]]))
        except Exception as e:
            print(f"❌ Error processing {pdf.name}: {e}")

    # Executive summary
    combined = " ".join(all_texts)
    executive_summary = processor._summarize(combined, max_sents=6)
    report.write("EXECUTIVE SUMMARY\n" + "-" * 60 + "\n")
    report.write(executive_summary + "\n\n")

    report.write("DOCUMENT ANALYSIS\n" + "-" * 60 + "\n\n")
    total_time = 0

    for name, res, proc_time in results:
        report.write(f"Document: {name} ({proc_time:.3f}s)\n")
        for i, sec in enumerate(res["sections"], 1):
            report.write(f"  {i}. {sec['section_title']}:\n")
            report.write(f"     Summary: {sec['summary']}\n\n")
        total_time += proc_time
        report.write("-" * 70 + "\n\n")

    avg_time = total_time / len(results) if results else 0
    report.write(f"Total Time: {total_time:.2f}s\nAvg Time per Document: {avg_time:.3f}s\n")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report.getvalue())

    pdf_path = export_pdf(report.getvalue(), "SmartPDF_Report.pdf")

    print(f"\n✅ Analysis complete!")
    print(f"📄 Text Report: {os.path.abspath(output_file)}")
    print(f"📘 PDF Report:  {os.path.abspath(pdf_path)}")
    print(f"⚙️  Total runtime: {total_time:.2f}s")

    return output_file, pdf_path


if __name__ == "__main__":
    generate_report()

