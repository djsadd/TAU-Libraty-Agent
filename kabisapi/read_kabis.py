# -*- coding: utf-8 -*-
import re
import html
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup  # pip install beautifulsoup4
import pandas as pd            # pip install pandas openpyxl

ISBN_RE = re.compile(r"ISBN\s+([0-9\-–—xX]+)")
YEAR_RE = re.compile(r"(\d{4})")
COUNT_RE = re.compile(r"(\d+)\s*экз", re.IGNORECASE)


def text_of(node) -> str:
    """Текст узла: с пробелами между блоками, без лишних пробелов."""
    if node is None:
        return ""
    s = node.get_text(" ", strip=True)
    return html.unescape(re.sub(r"\s+", " ", s).strip())


def clean_spaces(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", (s or "").strip()))


def parse_header_info(table: BeautifulSoup) -> Tuple[Optional[int], str, str, str]:
    """
    Возвращает (номер, bbk_top, dept_code, lang).
    - номер: число из левой колонки с class='num'
    - bbk_top: жирный код в первой строке (например '67.408')
    - dept_code: буква/сигла слева в ячейке 'align=right' (например 'К' или 'ЧМ' и т.п.)
    - lang: язык (рус/каз/eng...)
    """
    num = None
    bbk_top = ""
    dept_code = ""
    lang = ""

    # номер
    td_num = table.select_one("td.num")
    if td_num:
        try:
            num = int(text_of(td_num).split()[0])
        except Exception:
            pass

    # bbk (первый <b> после номера)
    # В шапке обычно: <td colspan=2><b>67.408</b></td>
    first_b = table.find("b")
    if first_b:
        bbk_top = clean_spaces(first_b.get_text())

    # справа: dept/lang
    right = None
    for td in table.find_all("td"):
        if td.get("align") == "right":
            right = td
            break
    if right:
        parts = text_of(right).split()
        if parts:
            dept_code = parts[0]
            if len(parts) > 1:
                lang = parts[-1]

    return num, bbk_top, dept_code, lang


def parse_author_title(bold_block: BeautifulSoup) -> Tuple[str, str]:
    """
    В <b> иногда: 'Автор, И.О. <br> Заглавие' — вернём (author, title).
    Если автор не обнаружен, кладём всё в title.
    """
    if bold_block is None:
        return "", ""
    # берём HTML внутри <b>, чтобы понять split по <br>
    parts = [clean_spaces(p) for p in bold_block.decode_contents().split("<br>")]
    parts = [clean_spaces(BeautifulSoup(p, "html.parser").get_text(" ", strip=True)) for p in parts]
    parts = [p for p in parts if p]
    if not parts:
        return "", ""

    if len(parts) == 1:
        # либо только заглавие, либо автор+заглавие слиты — эвристика:
        # если есть запятая и инициалы — считаем автором, но заголовок неизвестен.
        s = parts[0]
        if re.search(r"[А-ЯA-Z][а-яa-zё]+,\s*[А-ЯA-Z]\.\s*[А-ЯA-Z]\.", s):
            return s, ""
        return "", s

    author = parts[0]
    title = " ".join(parts[1:])
    return author, title


def parse_pub_info(after_bold_text: str) -> Dict[str, Any]:
    """
    Парсим публикационные сведения (город/издательство/год/страницы/роль и т.п.)
    Пример: '[Текст]: Учебное пособие / Р.А. Барсукова.- Астана: Ун-т "Туран-Астана", 2011.- 58 с.'
    Эвристически достаём год и всё остальное как строку.
    """
    info = clean_spaces(after_bold_text)
    m_isbn = ISBN_RE.search(info)
    isbn = m_isbn.group(1) if m_isbn else ""

    m_year = YEAR_RE.search(info)
    year = m_year.group(1) if m_year else ""

    return {
        "pub_info": info,
        "year": year,
        "isbn": isbn,
    }


def parse_subjects(block_text: str) -> List[str]:
    """
    После '1.' идут рубрики вида:
    '1. Уголовное право - - коррупция - ...'
    Разобьём по ' - ' и лишнее почистим.
    """
    s = clean_spaces(block_text)
    # убрать '1.' и подобные префиксы
    s = re.sub(r"^\s*\d+\.\s*", "", s)
    # заменить повторные дефисы
    s = re.sub(r"\-\s*\-\s*", " - ", s)
    # разбивка — грубо по ' - '
    parts = [p.strip(" .;—-") for p in s.split(" - ") if p.strip(" .;—-")]
    return parts


def parse_copies(div_10pt: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    В <div class=10pt> несколько <nobr>:
    '* АБ, 16 экз.' → {'location': 'АБ', 'count': 16}
    """
    res: List[Dict[str, Any]] = []
    if not div_10pt:
        return res
    for nobr in div_10pt.find_all("nobr"):
        t = text_of(nobr)
        # уберём ведущую '*'
        t = t.lstrip("*").strip()
        # ожидаем "АБ, 16 экз."
        if "," in t:
            location, tail = t.split(",", 1)
            location = clean_spaces(location)
            m = COUNT_RE.search(tail)
            cnt = int(m.group(1)) if m else None
            res.append({"location": location, "count": cnt})
        else:
            if t:
                res.append({"location": t, "count": None})
    return res


def parse_links(table: BeautifulSoup) -> Dict[str, Optional[str]]:
    """
    В div.desc79 могут быть 2 ссылки: 'Скачать' и 'Открыть'
    """
    dl_url = None
    open_url = None
    desc = table.select_one("div.desc79")
    if desc:
        for a in desc.find_all("a"):
            title = (a.get("title") or "").lower()
            href = a.get("href")
            if "скачать" in title:
                dl_url = href
            elif "открыть" in title:
                open_url = href
    return {"download_url": dl_url, "open_url": open_url}


def parse_bbk_tail(table: BeautifulSoup) -> str:
    """
    <p class='bak'>ББК 67.408</p>
    """
    p = table.select_one("p.bak")
    return text_of(p)


def parse_idbk(table: BeautifulSoup) -> Optional[int]:
    """
    В шапке есть <input name='IDBk' value=41>
    """
    inp = table.find("input", {"name": "IDBk"})
    if inp and inp.has_attr("value"):
        try:
            return int(inp["value"])
        except Exception:
            return None
    return None


def parse_card_html(card_html: str) -> Dict[str, Any]:
    """
    Главный парсер одной карточки.
    """
    soup = BeautifulSoup(card_html, "html.parser")
    table = soup.find("table")
    if table is None:
        # иногда может прилететь пусто — вернём минимум
        return {}

    pos_number, bbk_top, dept_code, lang = parse_header_info(table)

    # ячейка после nowrap/bold содержит автор/заглавие
    # берём первый <td colspan=2><b>...</b> в теле (не самый верхний bbk)
    bolds = table.find_all("b")
    # первый b — это bbk_top, а второй b обычно автор/заголовок
    author, title = "", ""
    if len(bolds) >= 2:
        author, title = parse_author_title(bolds[1])

    # собрать текст сразу после жирного (публикационные сведения)
    pub_info_text = ""
    if len(bolds) >= 2:
        accum = []
        # пройти по соседям второго <b> до <br> или конца строки
        for sib in bolds[1].next_siblings:
            if getattr(sib, "name", None) == "br":
                break
            accum.append(str(sib))
        pub_info_text = clean_spaces(BeautifulSoup("".join(accum), "html.parser").get_text(" ", strip=True))

    pub = parse_pub_info(pub_info_text)
    subjects_text = ""
    copies_div = table.select_one("div[class='10pt']") or table.find("div", {"class": "10pt"})
    # текст между концом публикационных сведений и блоком 10pt часто — это рубрики (1. ... - - ...).
    # Возьмём весь текст таблицы и вырежем кусок до <div class=10pt>.
    full_text = text_of(table)
    if copies_div:
        before_copies = text_of(copies_div.find_previous(string=True)) if copies_div.find_previous(string=True) else ""
        # fallback: если не нашли «предыдущий текст», используем общий текст и удалим из него содержимое copies_div
        full_no_copies = full_text.replace(text_of(copies_div), "")
        subjects_text = full_no_copies

    # попытаемся найти участок, начинающийся на "1." — это основной признак рубрик
    m_idx = re.search(r"\b1\.\s", subjects_text)
    subjects = []
    if m_idx:
        subjects = parse_subjects(subjects_text[m_idx.start():])

    copies = parse_copies(copies_div)
    links = parse_links(table)
    bbk_tail = parse_bbk_tail(table)
    idbk = parse_idbk(table)

    # доп. сигла в левой узкой колонке (например 'Ж83', 'С30' и т.п.)
    sigla = ""
    narrow_td = None
    for td in table.find_all("td"):
        if td.get("nowrap") is not None:
            narrow_td = td
            break
    if narrow_td:
        b = narrow_td.find("b")
        if b:
            sigla = clean_spaces(b.get_text())

    return {
        "pos": pos_number,
        "idbk": idbk,
        "bbk_top": bbk_top,
        "bbk_tail": bbk_tail,
        "dept_code": dept_code,
        "lang": lang,
        "sigla": sigla,
        "author": author,
        "title": title,
        "pub_info": pub["pub_info"],
        "year": pub["year"],
        "isbn": pub["isbn"],
        "subjects": "; ".join(subjects) if subjects else "",
        "copies": copies,                 # список словарей
        "download_url": links["download_url"],
        "open_url": links["open_url"],
    }


def parse_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Принимает твой JSON вида:
    {'Books': {'dbid': 'BOOKS', 'normalized_query': 'AllBooks', 'total': 13401, 'range': [{'pos': 1, 'card': '<table ...'}, ...]}}
    Возвращает список записей (словарей) по каждой карточке.
    """
    items = payload.get("Books", {}).get("range", [])
    rows: List[Dict[str, Any]] = []
    for it in items:
        card_html = it.get("card", "")
        row = parse_card_html(card_html)
        # если pos из HTML не распарсился — возьмём из обёртки
        if "pos" not in row or row["pos"] is None:
            row["pos"] = it.get("pos")
        rows.append(row)
    return rows


def flatten_copies(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Разворачивает copies в отдельные строки (удобно для Excel/аналитики).
    """
    out: List[Dict[str, Any]] = []
    for r in rows:
        copies = r.pop("copies", []) or []
        base = {k: v for k, v in r.items()}
        if not copies:
            out.append({**base, "copy_location": None, "copy_count": None})
            continue
        for c in copies:
            out.append({
                **base,
                "copy_location": c.get("location"),
                "copy_count": c.get("count"),
            })
    return out


def save_to_csv(rows: List[Dict[str, Any]], path: str) -> None:
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def save_to_xlsx(rows: List[Dict[str, Any]], path: str) -> None:
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)


# ---------------- пример запуска ----------------
if __name__ == "__main__":
    # сюда вставь твой объект payload; для примера — заглушка:
    sample_payload = {
        # ... твой JSON ...
    }

    rows = parse_payload(sample_payload)
    rows_flat = flatten_copies(rows)

    print(f"Распарсили карточек: {len(rows)}")
    # Сохраним
    save_to_csv(rows_flat, "kabis_books.csv")
    save_to_xlsx(rows_flat, "kabis_books.xlsx")
    print("Готово: kabis_books.csv, kabis_books.xlsx")
