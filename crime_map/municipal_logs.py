from __future__ import annotations

from pathlib import Path
import re
from typing import Callable
from urllib.parse import urljoin

import pandas as pd
import pdfplumber
import requests

from .cache import download_file
from .offense_mapping import classify_offense_series

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}
DOCUMENT_CENTER_LINK_RE = re.compile(r'(?P<href>/DocumentCenter/View/\d+(?:/[^"\'<>\s]+)?)')
DOCUMENT_ID_RE = re.compile(r"/DocumentCenter/View/(?P<id>\d+)")
BELMONT_INCIDENT_RE = re.compile(
    r"^Incident #:\s*\S+\s+Date:\s*(?P<date>\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}:\d{2}\s+Type:\s*(?P<crime>.+?)\s*$"
)
READING_HEADER_RE = re.compile(r"^\*\*\*\s+\w+\s+(?P<date>\d{2}/\d{2}/\d{4})\s+(?P<crime>.+?)\s*$")
LEXINGTON_CALL_RE = re.compile(r"^\d{2}-\d{6}$")
LEXINGTON_DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{2}$")
LEXINGTON_DATE_X_RANGE = (70.0, 145.0)
LEXINGTON_OFFENSE_X_RANGE = (154.0, 286.0)
LINE_GROUP_TOLERANCE = 2.0

BELMONT_LOG_PAGE_URLS = ("https://www.belmont-ma.gov/2225/Call-Log",)
LEXINGTON_LOG_PAGE_URLS = (
    "https://www.lexingtonma.gov/489/Weekly-Police-Logs",
    "https://www.lexingtonma.gov/2496/2025-Weekly-Police-Logs",
    "https://www.lexingtonma.gov/2278/2024-Weekly-Police-Logs",
    "https://www.lexingtonma.gov/1940/2023-Weekly-Police-Logs",
    "https://www.lexingtonma.gov/1941/2022-Weekly-Police-Logs",
)
READING_LOG_PAGE_URLS = ("https://www.readingma.gov/752/Daily-Police-Log",)


def _fetch_html(url: str) -> str:
    response = requests.get(url, timeout=120, headers=REQUEST_HEADERS)
    response.raise_for_status()
    return response.text


def _extract_document_center_urls(page_urls: tuple[str, ...]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for page_url in page_urls:
        html = _fetch_html(page_url)
        for match in DOCUMENT_CENTER_LINK_RE.finditer(html):
            absolute_url = urljoin(page_url, match.group("href"))
            if absolute_url in seen:
                continue
            seen.add(absolute_url)
            urls.append(absolute_url)

    return urls


def _document_id_from_url(url: str) -> str:
    match = DOCUMENT_ID_RE.search(url)
    if not match:
        raise ValueError(f"Could not determine DocumentCenter id from URL: {url}")
    return match.group("id")


def _download_pdf(city: str, url: str, *, force_refresh: bool = False) -> Path:
    document_id = _document_id_from_url(url)
    return download_file(
        url,
        filename=f"{city.lower()}_police_log_{document_id}.pdf",
        max_age_hours=168.0,
        force_refresh=force_refresh,
        timeout=120,
        headers=REQUEST_HEADERS,
    )


def _file_looks_like_pdf(pdf_path: Path) -> bool:
    return pdf_path.read_bytes()[:16].lstrip().startswith(b"%PDF")


def _group_words_by_line(words: list[dict[str, object]], tolerance: float = LINE_GROUP_TOLERANCE) -> list[list[dict[str, object]]]:
    lines: list[tuple[float, list[dict[str, object]]]] = []

    for word in sorted(words, key=lambda item: (float(item["top"]), float(item["x0"]))):
        top = float(word["top"])
        if not lines or abs(lines[-1][0] - top) > tolerance:
            lines.append((top, [word]))
            continue
        lines[-1][1].append(word)

    return [sorted(line_words, key=lambda item: float(item["x0"])) for _, line_words in lines]


def _normalize_log_frame(city: str, records: list[tuple[pd.Timestamp, str]]) -> pd.DataFrame:
    columns = ["City", "Date", "Crime", "Offense Group", "Macro Crime", "Neighborhood"]
    if not records:
        return pd.DataFrame(columns=columns)

    frame = pd.DataFrame(records, columns=["Date", "Crime"])
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce").dt.normalize()
    frame["Crime"] = frame["Crime"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    frame = frame[frame["Date"].notna() & frame["Crime"].ne("")].copy()
    classifications = classify_offense_series(city, frame["Crime"])
    frame["Offense Group"] = classifications["Offense Group"]
    frame["Macro Crime"] = classifications["Macro Crime"]
    frame["City"] = city
    frame["Neighborhood"] = city
    return frame[columns].sort_values(["Date", "Crime"], ignore_index=True)


def _extract_pdf_text(pdf_path: Path) -> str:
    with pdfplumber.open(str(pdf_path)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _parse_belmont_log_text(text: str) -> list[tuple[pd.Timestamp, str]]:
    records: list[tuple[pd.Timestamp, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = BELMONT_INCIDENT_RE.match(line)
        if not match:
            continue
        records.append((pd.to_datetime(match.group("date"), format="%Y-%m-%d"), match.group("crime")))
    return records


def _parse_reading_log_text(text: str) -> list[tuple[pd.Timestamp, str]]:
    records: list[tuple[pd.Timestamp, str]] = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        match = READING_HEADER_RE.match(line)
        if not match:
            continue
        crime = match.group("crime").rstrip("* ").strip()
        records.append((pd.to_datetime(match.group("date"), format="%m/%d/%Y"), crime))
    return records


def _parse_lexington_words(words: list[dict[str, object]]) -> list[tuple[pd.Timestamp, str]]:
    records: list[tuple[pd.Timestamp, str]] = []

    current_date: pd.Timestamp | None = None
    current_offense_parts: list[str] = []

    for line in _group_words_by_line(words):
        if not line:
            continue

        first_text = str(line[0].get("text", "")).strip()
        if LEXINGTON_CALL_RE.match(first_text):
            if current_date is not None and current_offense_parts:
                records.append((current_date, " ".join(current_offense_parts).strip()))
            current_date = None
            current_offense_parts = []
            for word in line:
                text = str(word.get("text", "")).strip()
                x0 = float(word["x0"])
                if (
                    LEXINGTON_DATE_X_RANGE[0] <= x0 < LEXINGTON_DATE_X_RANGE[1]
                    and LEXINGTON_DATE_RE.match(text)
                ):
                    current_date = pd.to_datetime(text, format="%m/%d/%y")
                if LEXINGTON_OFFENSE_X_RANGE[0] <= x0 < LEXINGTON_OFFENSE_X_RANGE[1]:
                    current_offense_parts.append(text)
            continue

        if current_date is None:
            continue

        continuation = [
            str(word.get("text", "")).strip()
            for word in line
            if LEXINGTON_OFFENSE_X_RANGE[0] <= float(word["x0"]) < LEXINGTON_OFFENSE_X_RANGE[1]
        ]
        if continuation:
            current_offense_parts.extend(continuation)

    if current_date is not None and current_offense_parts:
        records.append((current_date, " ".join(current_offense_parts).strip()))

    return records


def _parse_lexington_pdf(pdf_path: Path) -> list[tuple[pd.Timestamp, str]]:
    records: list[tuple[pd.Timestamp, str]] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            records.extend(_parse_lexington_words(page.extract_words(use_text_flow=True)))

    return records


def _load_city_pdf_logs(
    *,
    city: str,
    page_urls: tuple[str, ...],
    parser: Callable[[Path], list[tuple[pd.Timestamp, str]]],
    force_refresh: bool = False,
) -> pd.DataFrame:
    pdf_urls = _extract_document_center_urls(page_urls)
    if not pdf_urls:
        raise ValueError(f"No official PDF logs were found for {city}.")
    records: list[tuple[pd.Timestamp, str]] = []

    for pdf_url in pdf_urls:
        pdf_path = _download_pdf(city, pdf_url, force_refresh=force_refresh)
        if not _file_looks_like_pdf(pdf_path):
            continue
        records.extend(parser(pdf_path))

    if not records:
        raise ValueError(f"No parseable public-log records were found for {city}.")

    return _normalize_log_frame(city, records)


def _parse_belmont_pdf(pdf_path: Path) -> list[tuple[pd.Timestamp, str]]:
    return _parse_belmont_log_text(_extract_pdf_text(pdf_path))


def _parse_reading_pdf(pdf_path: Path) -> list[tuple[pd.Timestamp, str]]:
    return _parse_reading_log_text(_extract_pdf_text(pdf_path))


def load_belmont_crime(force_refresh: bool = False) -> pd.DataFrame:
    return _load_city_pdf_logs(
        city="Belmont",
        page_urls=BELMONT_LOG_PAGE_URLS,
        parser=_parse_belmont_pdf,
        force_refresh=force_refresh,
    )


def load_lexington_crime(force_refresh: bool = False) -> pd.DataFrame:
    return _load_city_pdf_logs(
        city="Lexington",
        page_urls=LEXINGTON_LOG_PAGE_URLS,
        parser=_parse_lexington_pdf,
        force_refresh=force_refresh,
    )


def load_reading_crime(force_refresh: bool = False) -> pd.DataFrame:
    return _load_city_pdf_logs(
        city="Reading",
        page_urls=READING_LOG_PAGE_URLS,
        parser=_parse_reading_pdf,
        force_refresh=force_refresh,
    )
