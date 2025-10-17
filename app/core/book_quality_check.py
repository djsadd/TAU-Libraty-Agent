import os, math, random, io
from dataclasses import dataclass
from typing import List, Optional, Tuple
import re

import charset_normalizer as chn
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  # стабильность langdetect
from ftfy import fix_text
from collections import Counter

# PDF
import fitz  # PyMuPDF
# OCR
import pytesseract
from pytesseract import Output
from PIL import Image

# Опционально для DOCX/EPUB
from docx import Document as DocxDocument
from ebooklib import epub
from app.core.config import settings

pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

import math
from collections import Counter


def is_scanned_pdf(path: str, min_text_per_page: int = 300, min_text_fraction: float = 0.3) -> bool:
    """Определяет, что PDF — скан (а не текстовый), без OCR."""
    try:
        doc = fitz.open(path)
    except Exception:
        return True  # битый PDF считаем как скан/нечитабельный

    n_pages = doc.page_count
    if n_pages == 0:
        return True

    pages_with_text = 0
    total_chars = 0
    image_pages = 0

    for i in range(min(n_pages, 10)):  # проверяем только первые 10 страниц для скорости
        page = doc.load_page(i)
        text = page.get_text("text")
        total_chars += len(text)
        if len(text.strip()) > min_text_per_page:
            pages_with_text += 1
        if len(page.get_images()) > 0:
            image_pages += 1

    avg_chars = total_chars / max(1, min(n_pages, 10))
    text_fraction = pages_with_text / max(1, min(n_pages, 10))

    # 🎯 Эвристика
    # - почти нет текста
    # - при этом есть изображения
    if text_fraction < min_text_fraction and image_pages > pages_with_text:
        return True

    if avg_chars < 200 and text_fraction < 0.4:
        return True

    return False


def text_entropy(text: str) -> float:
    text = text.lower()
    freq = Counter(text)
    total = len(text)
    probs = [f/total for f in freq.values()]
    return -sum(p * math.log2(p) for p in probs)


def text_repetition_score(text: str) -> float:
    """0 → нормальный текст, 1 → почти полностью повторяющийся"""
    words = [w.lower() for w in text.split() if len(w) > 2]
    if not words:
        return 1.0
    unique = len(set(words))
    return 1 - (unique / len(words))


def line_diversity_score(text: str) -> float:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return 1.0
    unique = len(set(lines))
    return unique / len(lines)


def dominant_word_ratio(text: str) -> float:
    words = [w.lower() for w in text.split() if w.isalpha()]
    if not words:
        return 1.0
    common = Counter(words).most_common(5)
    total = sum(freq for _, freq in common)
    return total / len(words)


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


def text_is_readable(metrics: dict, text: str) -> bool:
    rep_score = text_repetition_score(text)
    line_div = line_diversity_score(text)
    dom_ratio = dominant_word_ratio(text)

    return (
        metrics["len"] >= 1000 and
        metrics["printable_ratio"] >= 0.95 and
        metrics["alnum_ratio"] >= 0.60 and
        metrics["�_ratio"] < 0.005 and
        metrics["ctrl_ratio"] < 0.005 and
        3 <= metrics["avg_token_len"] <= 20 and
        rep_score < 0.6 and
        line_div > 0.3 and
        dom_ratio < 0.4
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


def pdf_extract_text_stats(path: str) -> PDFTextStats:
    doc = fitz.open(path)
    n = doc.page_count
    pages_with_text = 0
    total_chars = 0
    sample_text = []

    for i in range(n):
        page = doc.load_page(i)
        txt = page.get_text("text") or ""
        total_chars += len(txt)
        if len(txt.strip()) >= 50:
            pages_with_text += 1
        # добавим текст для анализа только с первых 5 страниц
        if i < 5:
            sample_text.append(txt)

    text_sample = " ".join(sample_text)
    rep_score = text_repetition_score(text_sample)
    entropy = text_entropy(text_sample)
    line_div = line_diversity_score(text_sample)

    # Вердикт без OCR
    if pages_with_text / max(1, n) >= 0.7 and total_chars >= 2000:
        verdict = "OK_TEXT_PDF"
    else:
        verdict = "SCANNED_OR_LOW_TEXT"

    # Проверка на мусор
    if total_chars / max(1, n) > 100_000 or rep_score > 0.8 or entropy < 2.0 or line_div < 0.3:
        verdict = "CORRUPTED_TEXT_LAYER"

    return PDFTextStats(
        n_pages=n,
        pages_with_text=pages_with_text,
        total_chars=total_chars,
        sample_ocr_avg_conf=None,
        sample_ocr_bad_frac=None,
        verdict=verdict
    )


def check_file(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    report = {"path": path, "ext": ext, "book_quality": "UNKNOWN"}

    # 1️⃣ Проверка, что файл существует и не пустой
    if not os.path.exists(path):
        report.update({"verdict": "MISSING_FILE", "book_quality": "REJECT"})
        return report

    if os.path.getsize(path) == 0:
        report.update({"verdict": "EMPTY_FILE", "book_quality": "REJECT"})
        return report

    if ext == ".pdf":
        try:
            if is_scanned_pdf(path):
                report.update({
                    "type": "pdf",
                    "verdict": "LIKELY_SCANNED",
                    "book_quality": "SKIP_LOAD"
                })
                return report
        except Exception as e:
            report.update({
                "type": "pdf",
                "verdict": "SCAN_DETECT_ERROR",
                "book_quality": "REJECT",
                "error": str(e)
            })
            return report

        pdf = pdf_extract_text_stats(path)
        avg_chars = pdf.total_chars / max(1, pdf.n_pages)

        # 💡 Фильтр качества PDF
        if avg_chars > 100_000:
            quality = "CORRUPTED_TEXT_LAYER"
            verdict = "SKIP_LOAD"
        elif pdf.pages_with_text == 0:
            quality = "EMPTY_OR_SCANNED"
            verdict = "SKIP_LOAD"
        elif pdf.verdict == "SCANNED_OR_LOW_TEXT":
            quality = "POOR"
            verdict = "SKIP_LOAD"
        else:
            quality = "GOOD"
            verdict = pdf.verdict

        report.update({
            "type": "pdf",
            "pages": pdf.n_pages,
            "pages_with_text": pdf.pages_with_text,
            "total_chars": pdf.total_chars,
            "avg_chars_per_page": round(avg_chars),
            "verdict": verdict,
            "book_quality": quality,
        })
        return report

    # 3️⃣ Текстовые форматы
    text = ""
    try:
        if ext == ".txt":
            text = read_txt(path)
        elif ext == ".docx":
            text = read_docx(path)
        elif ext == ".epub":
            text = read_epub(path)
        else:
            report.update({
                "type": "unknown",
                "verdict": "UNSUPPORTED",
                "book_quality": "REJECT"
            })
            return report
    except Exception as e:
        report.update({
            "type": "textlike",
            "verdict": "CORRUPTED_FILE",
            "book_quality": "REJECT",
            "error": str(e)
        })
        return report

    # 4️⃣ Проверка читаемости и качества текста
    text = fix_text(text)
    metrics = basic_text_metrics(text)
    entropy = text_entropy(text)
    rep_score = text_repetition_score(text)
    line_div = line_diversity_score(text)

    if text_is_readable(metrics, text) and entropy > 3.0 and rep_score < 0.6 and line_div > 0.3:
        verdict = "OK_TEXT"
        quality = "GOOD"
    elif entropy < 2.0 or rep_score > 0.8 or line_div < 0.2:
        verdict = "REPEATED_OR_LOW_QUALITY_TEXT"
        quality = "POOR"
    else:
        verdict = "BAD_TEXT"
        quality = "POOR"

    report.update({
        "type": "textlike",
        "chars": metrics["len"],
        "printable_ratio": round(metrics["printable_ratio"], 4),
        "alnum_ratio": round(metrics["alnum_ratio"], 4),
        "bad_char_ratio": round(metrics["�_ratio"], 6),
        "ctrl_ratio": round(metrics["ctrl_ratio"], 6),
        "avg_token_len": round(metrics["avg_token_len"], 2),
        "lang": metrics["lang"],
        "entropy": round(entropy, 3),
        "repetition_score": round(rep_score, 3),
        "line_diversity": round(line_div, 3),
        "verdict": verdict,
        "book_quality": quality
    })
    return report



