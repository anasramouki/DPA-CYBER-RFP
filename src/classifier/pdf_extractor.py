"""
PDF and Document Text Extractor for CyberRFP Maroc
Extracts first pages of RFP documents (DCE, CPS, RC) for deep classification.
"""
import os
from typing import Optional


def extract_document_text(file_path: str, max_pages: int = 4) -> str:
    """
    Extracts text from PDF or text file using PyMuPDF.
    If PDF is scanned (empty text layer), returns indicator for OCR fallback.
    """
    if not file_path or not os.path.exists(file_path):
        return ""

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()[:10000]
        except Exception:
            return ""

    if ext == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            pages_text = []
            pages_to_read = min(len(doc), max_pages)

            for i in range(pages_to_read):
                page = doc[i]
                text = page.get_text()
                if text and text.strip():
                    pages_text.append(text.strip())

            full_extracted = "\n\n".join(pages_text)
            
            # If text is too sparse, document might be a scanned image
            if len(full_extracted.strip()) < 50 and pages_to_read > 0:
                return "[Document scanné - Couche texte minimale ou absente]"
                
            return full_extracted[:15000]

        except Exception as e:
            return f"[Erreur lecture PDF: {str(e)}]"

    return ""
