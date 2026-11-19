from __future__ import annotations
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree as ET
import csv
import io
import json
import mimetypes
import re

class _VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.hidden += 1
    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.hidden:
            self.hidden -= 1
    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())

def media_type_for(filename: str) -> str:
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"

def source_type_for(filename: str, declared: str | None = None) -> str:
    if declared:
        return declared
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md", ".rst"}: return "note"
    if suffix in {".eml"}: return "email"
    if suffix in {".ics"}: return "calendar_record"
    if suffix in {".html", ".htm", ".url"}: return "webpage"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic"}: return "image"
    if suffix in {".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg"}: return "audio"
    if suffix in {".mp4", ".mov", ".mkv", ".webm"}: return "video"
    if suffix in {".json", ".csv", ".xlsx", ".docx", ".pdf", ".pptx", ".doc", ".xls", ".ppt"}: return "document"
    return "other"

def extract_text(data: bytes, filename: str, media_type: str | None = None):
    suffix = Path(filename).suffix.lower()
    media = media_type or media_type_for(filename)
    warnings = []
    try:
        if suffix in {".txt", ".md", ".rst", ".csv", ".json", ".log"}:
            text = data.decode("utf-8-sig")
            if suffix == ".json":
                try:
                    text = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
                except Exception:
                    warnings.append("JSON parse failed; retained decoded text.")
            return text, "extracted", media, warnings
        if suffix in {".html", ".htm"}:
            parser = _VisibleHTML()
            parser.feed(data.decode("utf-8", errors="replace"))
            return "\n".join(parser.parts), "extracted", media, warnings
        if suffix == ".eml":
            msg = BytesParser(policy=policy.default).parsebytes(data)
            body_parts = []
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try: body_parts.append(part.get_content())
                        except Exception: pass
            elif msg.get_content_type() == "text/plain":
                try: body_parts.append(msg.get_content())
                except Exception: pass
            header = "\n".join(f"{k}: {msg.get(k)}" for k in ("From", "To", "Date", "Subject") if msg.get(k))
            return (header + "\n\n" + "\n".join(body_parts)).strip(), "extracted", media, warnings
        if suffix == ".docx":
            try:
                with ZipFile(io.BytesIO(data)) as zf:
                    xml = zf.read("word/document.xml")
                root = ET.fromstring(xml)
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                paragraphs = []
                for para in root.findall(".//w:p", ns):
                    line = "".join(node.text or "" for node in para.findall(".//w:t", ns))
                    if line.strip(): paragraphs.append(line)
                return "\n".join(paragraphs), "extracted", media, warnings
            except (BadZipFile, KeyError, ET.ParseError):
                return None, "extractor_failed", media, ["DOCX structure could not be read."]
        if suffix == ".ics":
            text = data.decode("utf-8", errors="replace")
            lines = [re.sub(r"^([^:]+):", r"\1: ", x) for x in text.splitlines() if x and not x.startswith(("BEGIN:", "END:", "VERSION:"))]
            return "\n".join(lines), "extracted", media, warnings
        # PDF, images, audio and video are preserved as source files. OCR/ASR is a separate adapter.
        return None, "awaiting_extractor", media, ["No OCR / speech-to-text / PDF extractor is bundled in this transitional runtime."]
    except UnicodeDecodeError:
        return None, "awaiting_extractor", media, ["File is not supported as UTF-8 text; original bytes were preserved."]

def chunk_text(text: str, max_chars: int = 2400):
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = max(text.rfind("\n", start, end), text.rfind("。", start, end), text.rfind(" ", start, end))
            if boundary > start + max_chars // 2:
                end = boundary + 1
        chunks.append((start, end, text[start:end]))
        start = end
    return chunks
