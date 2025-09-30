import os, math, random, io
from dataclasses import dataclass
from typing import List, Optional, Tuple

import charset_normalizer as chn
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  # стабильность langdetect
from ftfy import fix_text

# PDF
import fitz  # PyMuPDF
# OCR
import pytesseract
from pytesseract import Output
from PIL import Image

# Опционально для DOCX/EPUB
from docx import Document as DocxDocument
from ebooklib import epub
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------- Метрики текста ----------
def basic_text_metrics(text: str) -> dict:
    if not text:
        return {
            "len": 0, "printable_ratio": 0, "alnum_ratio": 0, "�_ratio": 0,
            "ctrl_ratio": 1, "avg_token_len": 0, "lang": None
        }
    n = len(text)
    printable = sum(1 for c in text if c.isprintable())
    alnum = sum(1 for c in text if c.isalnum())
    bad = text.count("�")
    ctrl = sum(1 for c in text if (ord(c) < 32 and c not in ("\n", "\r", "\t")))
    tokens = [t for t in text.split() if t]
    avg_tok = (sum(len(t) for t in tokens) / len(tokens)) if tokens else 0
    lang = None
    try:
        lang = detect(text[: min(5000, n)])
    except Exception:
        lang = None
    return {
        "len": n,
        "printable_ratio": printable / n if n else 0,
        "alnum_ratio": alnum / n if n else 0,
        "�_ratio": bad / n if n else 0,
        "ctrl_ratio": ctrl / n if n else 0,
        "avg_token_len": avg_tok,
        "lang": lang,
    }

def text_is_readable(metrics: dict) -> bool:
    return (
        metrics["len"] >= 1000 and
        metrics["printable_ratio"] >= 0.95 and
        metrics["alnum_ratio"] >= 0.60 and
        metrics["�_ratio"] < 0.005 and
        metrics["ctrl_ratio"] < 0.005 and
        3 <= metrics["avg_token_len"] <= 20
    )

# ---------- TXT/DOCX/EPUB ----------
def read_txt(path: str) -> str:
    raw = open(path, "rb").read()
    best = chn.from_bytes(raw).best()
    text = str(best) if best else raw.decode("utf-8", errors="ignore")
    return fix_text(text)

def read_docx(path: str) -> str:
    try:
        doc = DocxDocument(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        # Если это не настоящий DOCX или файл битый
        print(f"[WARN] read_docx: {path} не удалось прочитать ({e})")
        return ""


def read_epub(path: str) -> str:
    book = epub.read_epub(path)
    buf = []
    for item in book.get_items():
        if item.get_type() == epub.EpubHtml:
            try:
                buf.append(item.get_body_content().decode("utf-8", errors="ignore"))
            except Exception:
                pass
    # очень грубо: убрать теги
    import re
    text = re.sub(r"<[^>]+>", " ", " ".join(buf))
    return fix_text(text)

# ---------- PDF ----------
@dataclass
class PDFTextStats:
    n_pages: int
    pages_with_text: int
    total_chars: int
    sample_ocr_avg_conf: Optional[float]
    sample_ocr_bad_frac: Optional[float]
    verdict: str


def pdf_extract_text_stats(path: str, sample_pages_for_ocr: int = 6) -> PDFTextStats:
    doc = fitz.open(path)
    n = doc.page_count
    pages_with_text = 0
    total_chars = 0
    pages_no_text = []

    for i in range(n):
        page = doc.load_page(i)
        txt = page.get_text("text") or ""
        total_chars += len(txt)
        if len(txt.strip()) >= 50:
            pages_with_text += 1
        else:
            pages_no_text.append(i)

    # Евристика: если ≥70% страниц без текста — это «скан»
    scanned_likely = (n > 0 and len(pages_no_text) / n >= 0.7)

    ocr_avg_conf = None
    ocr_bad_frac = None

    if scanned_likely and n > 0:
        # Возьмём равномерную выборку страниц для OCR
        k = min(sample_pages_for_ocr, len(pages_no_text))
        sample_idxs = (
            random.sample(pages_no_text, k)
            if len(pages_no_text) >= k else pages_no_text
        )
        confs = []
        bad = 0
        for idx in sample_idxs:
            page = doc.load_page(idx)
            # render (dpi 200–300)
            pix = page.get_pixmap(dpi=250)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            # язык под себя: rus+kaz+eng при необходимости
            data = pytesseract.image_to_data(img, lang="rus+kaz+eng", output_type=Output.DATAFRAME)
            # фильтруем валидные элементы
            vals = [c for c in data.get("conf", []) if isinstance(c, (int, float))]
            if not vals:
                bad += 1
                continue
            # Tesseract даёт -1 для «мусора»
            page_confs = [v for v in vals if v >= 0]
            if not page_confs:
                bad += 1
                continue
            confs.append(sum(page_confs) / len(page_confs))
        if confs:
            ocr_avg_conf = sum(confs) / len(confs)
        if sample_idxs:
            ocr_bad_frac = bad / len(sample_idxs)

    # Вердикт
    if pages_with_text / max(1, n) >= 0.7 and total_chars >= 2000:
        verdict = "OK_TEXT_PDF"
    elif scanned_likely and ocr_avg_conf is not None:
        if ocr_avg_conf >= 70 and (ocr_bad_frac or 0) <= 0.3:
            verdict = "OK_OCR"
        elif ocr_avg_conf >= 50:
            verdict = "LOW_OCR"
        else:
            verdict = "BAD_OCR"
    elif scanned_likely:
        verdict = "SCANNED_NEEDS_OCR"
    else:
        # смешанный случай/тонкий PDF
        verdict = "UNCLEAR_TRY_OCR_OR_RETRY_EXTRACT"

    return PDFTextStats(
        n_pages=n,
        pages_with_text=pages_with_text,
        total_chars=total_chars,
        sample_ocr_avg_conf=ocr_avg_conf,
        sample_ocr_bad_frac=ocr_bad_frac,
        verdict=verdict,
    )


def check_file(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    report = {"path": path, "ext": ext}

    if ext == ".pdf":
        pdf = pdf_extract_text_stats(path)
        report.update({
            "type": "pdf",
            "pages": pdf.n_pages,
            "pages_with_text": pdf.pages_with_text,
            "total_chars": pdf.total_chars,
            "ocr_avg_conf": pdf.sample_ocr_avg_conf,
            "ocr_bad_frac": pdf.sample_ocr_bad_frac,
            "verdict": pdf.verdict
        })
        return report

    # Текстовые форматы
    text = ""
    if ext in (".txt",):
        text = read_txt(path)
    elif ext in (".docx",):
        text = read_docx(path)
    elif ext in (".epub",):
        text = read_epub(path)
    else:
        report.update({"type": "unknown", "verdict": "UNSUPPORTED"})
        return report

    text = fix_text(text)
    metrics = basic_text_metrics(text)

    if text_is_readable(metrics):
        verdict = "OK_TEXT"
    else:
        verdict = "BAD_TEXT"

    report.update({
        "type": "textlike",
        "chars": metrics["len"],
        "printable_ratio": round(metrics["printable_ratio"], 4),
        "alnum_ratio": round(metrics["alnum_ratio"], 4),
        "bad_char_ratio": round(metrics["�_ratio"], 6),
        "ctrl_ratio": round(metrics["ctrl_ratio"], 6),
        "avg_token_len": round(metrics["avg_token_len"], 2),
        "lang": metrics["lang"],
        "verdict": verdict
    })
    return report


