import streamlit as st
import time, tempfile, base64
from pathlib import Path
from pdf_processor import PDFProcessor  
from io import StringIO

st.set_page_config(
    page_title="SmartPDF_Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

col1, col2 = st.columns([1, 5])
with col1:
    st.image("logo.png", width=90)  
with col2:
    st.markdown("""
        # **SmartPDF_Analyzer**
        Your local, intelligent PDF summarization & insight generator.
        _Fast, private, and 100% offline._
    """)

st.markdown("---")

with st.sidebar:
    st.header("⚙️ Configuration")
    persona = st.text_input("👤 Persona", placeholder="e.g. Research Analyst")
    job = st.text_input("🎯 Job To Be Done", placeholder="e.g. Summarize and extract insights from academic papers")
    uploaded_files = st.file_uploader("📂 Upload PDF Files", type=["pdf"], accept_multiple_files=True)
    run_button = st.button("🚀 Run Smart Analysis")
    st.markdown("---")
    st.caption("Developed by *Om Dhanawat*")

def download_button(text, filename="SmartPDF_Report.txt"):
    """Creates a Streamlit download button for report."""
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">📥 Download Full Report</a>'
    st.markdown(href, unsafe_allow_html=True)

if run_button:
    if not persona or not job:
        st.error("⚠️ Please provide both Persona and Job To Be Done before running.")
    elif not uploaded_files:
        st.warning("📎 Please upload at least one PDF file to analyze.")
    else:
        st.success(f"Processing {len(uploaded_files)} PDF(s)...")

        processor = PDFProcessor(persona=persona, job=job)
        total_time, results = 0.0, []
        progress = st.progress(0)
        report = StringIO()
        report.write("DOCUMENT ANALYSIS REPORT\n\n")
        report.write(f"Persona: {persona}\nJob To Be Done: {job}\n\n")
        report.write(f"Processed Files: {', '.join([f.name for f in uploaded_files])}\n")
        report.write("============================================================\n\n")

        for i, pdf in enumerate(uploaded_files):
            progress.progress((i + 1) / len(uploaded_files))
            st.info(f"⏳ Processing: {pdf.name}")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf.read())
                pdf_path = tmp.name

            start = time.time()
            try:
                result = processor.process_pdf(pdf_path)
                elapsed = round(time.time() - start, 3)
                total_time += elapsed
                results.append((pdf.name, result, elapsed))

                # Write to report
                report.write(f"Document: {pdf.name} ({elapsed}s)\nSections:\n")
                for idx, sec in enumerate(result["sections"], 1):
                    report.write(f"  {idx}. {sec['section_title']}:\n     Summary: {sec['summary']}\n\n")
                report.write("------------------------------------------------------------\n\n")

                st.success(f"✅ Done: {pdf.name} ({elapsed}s)")
            except Exception as e:
                st.error(f"❌ Failed to process {pdf.name}: {e}")

        progress.progress(1.0)
        avg_time = round(total_time / max(len(results), 1), 3)

        st.markdown("## 📊 Summary Report")
        for doc_name, result, elapsed in results:
            st.markdown(f"### 📘 {doc_name} ({elapsed}s)")
            for i, sec in enumerate(result["sections"], 1):
                with st.expander(f"🔹 {sec['section_title']}"):
                    st.write(sec["summary"])

        st.markdown("---")
        st.markdown(f"**Total Time:** {round(total_time, 2)}s | **Average per Document:** {avg_time}s")
        st.success("🎉 Analysis complete!")

        # Download option
        download_button(report.getvalue(), filename="SmartPDF_Report.txt")
