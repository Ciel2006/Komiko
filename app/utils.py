import os
import re
from pathlib import Path


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text


def get_comic_extensions():
    return {".cbz", ".cbr", ".epub"}


def get_image_extensions():
    return {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def safe_path(path_str):
    try:
        return os.path.normpath(path_str)
    except Exception:
        return path_str