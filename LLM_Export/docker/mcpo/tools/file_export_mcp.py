import os
import uuid
import emoji
import datetime
import zipfile
import py7zr
import logging
import threading
import markdown2
from bs4 import BeautifulSoup
import time
from mcp.server.fastmcp import FastMCP
from openpyxl import Workbook
import csv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

PERSISTENT_FILES = os.getenv("PERSISTENT_FILES", "false")
FILES_DELAY = int(os.getenv("FILES_DELAY", 60)) 

EXPORT_DIR_ENV = os.getenv("FILE_EXPORT_DIR")
EXPORT_DIR = (EXPORT_DIR_ENV or r"/output").rstrip("/")
os.makedirs(EXPORT_DIR, exist_ok=True)


BASE_URL_ENV = os.getenv("FILE_EXPORT_BASE_URL")
BASE_URL = (BASE_URL_ENV or "http://localhost:9003/files").rstrip("/")

LOG_LEVEL_ENV = os.getenv("LOG_LEVEL")  # e.g., DEBUG, INFO, WARNING, 10, etc.
LOG_FORMAT_ENV = os.getenv(
    "LOG_FORMAT", "%(asctime)s %(levelname)s %(name)s - %(message)s"
)

def _resolve_log_level(val: str | None) -> int:
    if not val:
        return logging.INFO
    v = val.strip()
    if v.isdigit():
        try:
            return int(v)
        except ValueError:
            return logging.INFO
    return getattr(logging, v.upper(), logging.INFO)

logging.basicConfig(
    level=_resolve_log_level(LOG_LEVEL_ENV),
    format=LOG_FORMAT_ENV,
)

log = logging.getLogger("file_export_mcp")
log.setLevel(_resolve_log_level(LOG_LEVEL_ENV))
log.info("Effective LOG_LEVEL -> %s", logging.getLevelName(log.level))

mcp = FastMCP("file_export")


def _public_url(folder_path: str, filename: str) -> str:
    """Build a stable public URL for a generated file."""
    folder = os.path.basename(folder_path).lstrip("/")
    name = filename.lstrip("/")
    return f"{BASE_URL}/{folder}/{name}"

def _generate_unique_folder() -> str:
    folder_name = f"export_{uuid.uuid4().hex[:10]}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    folder_path = os.path.join(EXPORT_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def _generate_filename(folder_path: str, ext: str, filename: str = None) -> tuple[str, str]:
    if not filename:
        filename = f"export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

    base, ext = os.path.splitext(filename)
    filepath = os.path.join(folder_path, filename)
    counter = 1

    while os.path.exists(filepath):
        filename = f"{base}_{counter}{ext}"
        filepath = os.path.join(folder_path, filename)
        counter += 1

    return filepath, filename

styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
name="CustomHeading1",
parent=styles["Heading1"],
textColor=colors.HexColor("#0A1F44"),
spaceAfter=12
))

styles.add(ParagraphStyle(
name="CustomHeading2",
parent=styles["Heading2"],
textColor=colors.HexColor("#1C3F77"),
spaceAfter=10
))

styles.add(ParagraphStyle(
name="CustomHeading3",
parent=styles["Heading3"],
textColor=colors.HexColor("#3A6FB0"), 
spaceAfter=8
))

styles.add(ParagraphStyle(
name="CustomNormal",
parent=styles["Normal"],
fontSize=11,
leading=14
))

def render_html_element(elem):
    if elem.name == "img":
        src = elem.get("src")
        try:
            img = Image(src, width=200, height=150) 
            return img
        except Exception:
            return Paragraph("[Image not found]", styles["CustomNormal"])
    elif elem.name == "h1":
        return Paragraph(render_text_with_emojis(elem.get_text()), styles["CustomHeading1"])
    elif elem.name == "h2":
        return Paragraph(render_text_with_emojis(elem.get_text()), styles["CustomHeading2"])
    elif elem.name == "h3":
        return Paragraph(render_text_with_emojis(elem.get_text()), styles["CustomHeading3"])
    else:
        return Paragraph(render_text_with_emojis(elem.get_text()), styles["CustomNormal"])

def render_text_with_emojis(text: str) -> str:
    return emoji.emojize(text, language="alias")


def _cleanup_files(folder_path: str, delay_minutes: int):
    """Deletes files in a folder after a specified time."""
    def delete_files():
        time.sleep(delay_minutes * 60)
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    os.remove(os.path.join(root, file))
            os.rmdir(folder_path)
        except Exception as e:
            logging.error(f"Error deleting files : {e}")

    thread = threading.Thread(target=delete_files)
    thread.start()

@mcp.tool()
def create_excel(data: list[list[str]], filename: str = None, persistent: bool = PERSISTENT_FILES) -> dict:
    folder_path = _generate_unique_folder()
    filepath, fname = _generate_filename(folder_path, "xlsx", filename)
    wb = Workbook()
    ws = wb.active
    for row in data:
        ws.append(row)
    wb.save(filepath)
    
    if not persistent:
        _cleanup_files(folder_path, FILES_DELAY)
    
    return {"url": _public_url(folder_path, fname)}

@mcp.tool()
def create_csv(data: list[list[str]], filename: str = None, persistent: bool = PERSISTENT_FILES) -> dict:
    folder_path = _generate_unique_folder()
    filepath, fname = _generate_filename(folder_path, "csv", filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(data)
    
    if not persistent:
        _cleanup_files(folder_path, FILES_DELAY)
    
    return {"url": _public_url(folder_path, fname)}

@mcp.tool()
def create_pdf(text: list[str], filename: str = None, persistent: bool = PERSISTENT_FILES) -> dict:
    folder_path = _generate_unique_folder()
    filepath, fname = _generate_filename(folder_path, "pdf", filename)

    md_text = "\n".join(text)
    html = markdown2.markdown(md_text)
    soup = BeautifulSoup(html, "html.parser")

    story = []
    for elem in soup.contents:
        block = render_html_element(elem)
        if block:
            story.append(block)
            story.append(Spacer(1, 6))

    doc = SimpleDocTemplate(filepath)
    doc.build(story)

    if not persistent:
        _cleanup_files(folder_path, FILES_DELAY)

    return {"url": _public_url(folder_path, fname)}

@mcp.tool()
def create_file(content: str, filename: str, persistent: bool = PERSISTENT_FILES) -> dict:
    folder_path = _generate_unique_folder()
    base, ext = os.path.splitext(filename)
    filepath = os.path.join(folder_path, filename)
    counter = 1

    while os.path.exists(filepath):
        filename = f"{base}_{counter}{ext}"
        filepath = os.path.join(folder_path, filename)
        counter += 1

    if ext.lower() == ".xml" and not content.strip().startswith("<?xml"):
        content = f'<?xml version="1.0" encoding="UTF-8"?>\n{content}'

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    if not persistent:
        _cleanup_files(folder_path, FILES_DELAY)
    
    return {"url": _public_url(folder_path, filename)}

@mcp.tool()
def generate_and_archive(files_data: list[dict], archive_format: str = "zip", archive_name: str = None, persistent: bool = PERSISTENT_FILES) -> dict:
    folder_path = _generate_unique_folder()
    
    generated_files = []
    
    for file_info in files_data:
        filename = file_info.get("filename")
        content = file_info.get("content")
        format_type = file_info.get("format")
 
        if content is None:
            content = ""        

        filepath, fname = _generate_filename(folder_path, format_type, filename)
        
        if format_type == "py" or format_type == "cs" or format_type == "txt":
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        elif format_type == "pdf":
            doc = SimpleDocTemplate(filepath)
            styles = getSampleStyleSheet()
            story = []
            if isinstance(content, list):
                for t in content:
                    story.append(Paragraph(t, styles["Normal"]))
                    story.append(Spacer(1, 12))
            else:
                story.append(Paragraph(content, styles["Normal"]))
                story.append(Spacer(1, 12))
            doc.build(story)
        elif format_type == "xlsx":
            wb = Workbook()
            ws = wb.active
            if isinstance(content, list):
                for row in content:
                    ws.append(row)
            wb.save(filepath)
        elif format_type == "csv":
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                if isinstance(content, list):
                    csv.writer(f).writerows(content)
                else:
                    csv.writer(f).writerow([content])
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        
        generated_files.append(filepath)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if archive_format.lower() == "7z":
        archive_filename = f"{archive_name or 'archive'}_{timestamp}.7z"
        archive_path = os.path.join(folder_path, archive_filename)
        with py7zr.SevenZipFile(archive_path, mode='w') as archive:
            for file_path in generated_files:
                archive.write(file_path, os.path.basename(file_path))
    elif archive_format.lower() == "tar.gz":
        archive_filename = f"{archive_name or 'archive'}_{timestamp}.tar.gz"
        archive_path = os.path.join(folder_path, archive_filename)
        with tarfile.open(archive_path, "w:gz") as tar:
            for file_path in generated_files:
                tar.add(file_path, arcname=os.path.basename(file_path))
    else: 
        archive_filename = f"{archive_name or 'archive'}_{timestamp}.zip"
        archive_path = os.path.join(folder_path, archive_filename)
        with zipfile.ZipFile(archive_path, 'w') as zipf:
            for file_path in generated_files:
                zipf.write(file_path, os.path.basename(file_path))
    
    if not persistent:
        _cleanup_files(folder_path, FILES_DELAY)
        
    return {"url": _public_url(folder_path, archive_filename)}

if __name__ == "__main__":
    mcp.run()
