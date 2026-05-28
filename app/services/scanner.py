import os
import re
from pathlib import Path
from app.models import db, Library, Comic, Chapter, Page


CHAPTER_PATTERNS = [
    re.compile(r"ch\.?\s*(\d+\.?\d*)", re.IGNORECASE),
    re.compile(r"chapter\s*(\d+\.?\d*)", re.IGNORECASE),
    re.compile(r"chap\s*(\d+\.?\d*)", re.IGNORECASE),
    re.compile(r"^(\d+\.?\d*)", re.IGNORECASE),
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
COMIC_EXTENSIONS = {".cbz", ".cbr", ".epub"}


def extract_chapter_number(filename):
    stem = Path(filename).stem
    for pattern in CHAPTER_PATTERNS:
        match = pattern.search(stem)
        if match:
            return float(match.group(1))
    return None


def is_image_file(path):
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def is_comic_file(path):
    return Path(path).suffix.lower() in COMIC_EXTENSIONS


def get_images_in_directory(dir_path):
    if not os.path.isdir(dir_path):
        return []
    images = []
    for f in sorted(os.listdir(dir_path)):
        full = os.path.join(dir_path, f)
        if os.path.isfile(full) and is_image_file(full):
            images.append(full)
    return images


def get_archive_type(path):
    ext = Path(path).suffix.lower()
    if ext == ".epub":
        return "epub"
    if ext in (".cbz", ".cbr"):
        return "cbz"
    return None


def scan_library(library_id):
    library = Library.query.get(library_id)
    if not library:
        return None, "Library not found"

    root = Path(library.path)
    if not root.exists():
        return None, f"Path does not exist: {library.path}"

    existing_comics = {c.folder_path: c.id for c in Comic.query.filter_by(library_id=library.id).all()}

    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue

        comic_path = str(entry.resolve())
        if comic_path in existing_comics:
            comic = Comic.query.get(existing_comics[comic_path])
        else:
            comic = Comic(
                library_id=library.id,
                title=entry.name,
                folder_path=comic_path,
            )
            db.session.add(comic)
            db.session.flush()

        _scan_comic(comic)

    db.session.commit()
    return library, None


def _scan_comic(comic):
    comic_path = Path(comic.folder_path)

    chapters_found = []

    archive_files = [f for f in sorted(comic_path.iterdir()) if f.is_file() and is_comic_file(f)]
    subdirs = [f for f in sorted(comic_path.iterdir()) if f.is_dir()]

    for arch in archive_files:
        atype = get_archive_type(arch)
        ch_num = extract_chapter_number(arch.name)
        if ch_num is None:
            ch_num = float(len(chapters_found) + 1)
        chapters_found.append({
            "number": ch_num,
            "title": arch.stem,
            "path": str(arch.resolve()),
            "type": atype,
        })

    for subdir in subdirs:
        child_archives = [f for f in sorted(subdir.iterdir()) if f.is_file() and is_comic_file(f)]
        has_images = any(is_image_file(str(f)) for f in subdir.iterdir() if f.is_file())

        if child_archives:
            for f in child_archives:
                atype = get_archive_type(f)
                ch_num = extract_chapter_number(f.name)
                if ch_num is None:
                    ch_num = extract_chapter_number(subdir.name)
                if ch_num is None:
                    ch_num = float(len(chapters_found) + 1)
                chapters_found.append({
                    "number": ch_num,
                    "title": f.stem,
                    "path": str(f.resolve()),
                    "type": atype,
                })
        elif has_images:
            ch_num = extract_chapter_number(subdir.name)
            if ch_num is None:
                ch_num = float(len(chapters_found) + 1)
            chapters_found.append({
                "number": ch_num,
                "title": subdir.name,
                "path": str(subdir.resolve()),
                "type": "folder",
            })

    existing_chapters = {c.id: c for c in Chapter.query.filter_by(comic_id=comic.id).all()}
    existing_paths = {c.folder_path: c for c in existing_chapters.values()}

    for ch_data in chapters_found:
        if ch_data["path"] in existing_paths:
            chapter = existing_paths[ch_data["path"]]
            chapter.chapter_number = ch_data["number"]
            chapter.title = ch_data["title"]
        else:
            chapter = Chapter(
                comic_id=comic.id,
                chapter_number=ch_data["number"],
                title=ch_data["title"],
                folder_path=ch_data["path"],
            )
            db.session.add(chapter)
            db.session.flush()

        _scan_chapter_pages(chapter, ch_data["type"])

    chapter_count = len(chapters_found)
    comic.cover_path = _find_cover(comic, chapters_found)


def _scan_chapter_pages(chapter, chapter_type):
    page_count = 0
    if chapter_type == "folder":
        images = get_images_in_directory(chapter.folder_path)
        for i, img_path in enumerate(images, 1):
            existing = Page.query.filter_by(chapter_id=chapter.id, page_number=i).first()
            if not existing:
                page = Page(chapter_id=chapter.id, page_number=i, file_path=img_path)
                db.session.add(page)
            page_count += 1
    elif chapter_type == "cbz":
        import zipfile
        try:
            with zipfile.ZipFile(chapter.folder_path, "r") as zf:
                image_names = sorted(
                    n for n in zf.namelist()
                    if not n.startswith("__MACOSX") and Path(n).suffix.lower() in IMAGE_EXTENSIONS
                )
                for i, name in enumerate(image_names, 1):
                    existing = Page.query.filter_by(chapter_id=chapter.id, page_number=i).first()
                    if not existing:
                        page = Page(
                            chapter_id=chapter.id,
                            page_number=i,
                            file_path=f"{chapter.folder_path}!{name}",
                        )
                        db.session.add(page)
                    page_count += 1
        except zipfile.BadZipFile:
            pass
    elif chapter_type == "epub":
        from app.services.comic_parser import parse_epub_page_order
        pages_data = parse_epub_page_order(chapter.folder_path)
        for i, (img_path_in_zip, _) in enumerate(pages_data, 1):
            existing = Page.query.filter_by(chapter_id=chapter.id, page_number=i).first()
            if not existing:
                page = Page(
                    chapter_id=chapter.id,
                    page_number=i,
                    file_path=f"{chapter.folder_path}!{img_path_in_zip}",
                )
                db.session.add(page)
            page_count += 1

    chapter.page_count = page_count


def _find_cover(comic, chapters_found):
    from app.services.comic_parser import extract_cover

    for ch_data in chapters_found:
        cover = extract_cover(comic, ch_data)
        if cover:
            return cover
    return None