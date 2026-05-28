import os
import zipfile
from pathlib import Path
from flask import current_app
from PIL import Image
import io


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def parse_epub_page_order(epub_path):
    from lxml import etree

    try:
        with zipfile.ZipFile(epub_path, "r") as zf:
            container_xml = zf.read("META-INF/container.xml")
            container = etree.fromstring(container_xml)
            ns = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile_el = container.find(".//c:rootfile", ns)
            if rootfile_el is None:
                rootfile_el = container.find(".//rootfile")
            if rootfile_el is None:
                return []

            opf_path = rootfile_el.get("full-path")
            opf_dir = str(Path(opf_path).parent)
            opf_xml = zf.read(opf_path)
            opf = etree.fromstring(opf_xml)

            nsmap = opf.nsmap.get(None) or ""
            if nsmap:
                ns_prefix = f"{{{nsmap}}}"
            else:
                ns_prefix = ""

            manifest = {}
            for item in opf.findall(f"{ns_prefix}manifest/{ns_prefix}item"):
                item_id = item.get("id")
                href = item.get("href")
                media_type = item.get("media-type", "")
                properties = item.get("properties", "")
                manifest[item_id] = {
                    "href": href,
                    "media_type": media_type,
                    "properties": properties,
                }

            spine_ids = []
            for itemref in opf.findall(f"{ns_prefix}spine/{ns_prefix}itemref"):
                idref = itemref.get("idref")
                if idref:
                    spine_ids.append(idref)

            image_items = []
            for item_id, item in manifest.items():
                if item["media_type"].startswith("image/"):
                    image_items.append(item_id)

            if not spine_ids:
                sorted_images = sorted(
                    image_items,
                    key=lambda iid: manifest[iid]["href"]
                )
                spine_ids = sorted_images

            pages = []
            seen_hrefs = set()
            for item_id in spine_ids:
                if item_id not in manifest:
                    continue
                item = manifest[item_id]
                href = item["href"]
                if opf_dir:
                    full_href = f"{opf_dir}/{href}"
                else:
                    full_href = href

                if item["media_type"].startswith("image/") and full_href not in seen_hrefs:
                    pages.append((full_href, item["media_type"]))
                    seen_hrefs.add(full_href)

            if not pages:
                all_entries = sorted(zf.namelist())
                pages = []
                for name in all_entries:
                    if Path(name).suffix.lower() in IMAGE_EXTENSIONS and not name.startswith("__MACOSX"):
                        pages.append((name, ""))
                seen2 = set()
                deduped = []
                for p in pages:
                    if p[0] not in seen2:
                        deduped.append(p)
                        seen2.add(p[0])
                return deduped

            return pages

    except (zipfile.BadZipFile, KeyError, Exception):
        return []


def extract_cover(comic, chapter_data):
    cover_dir = current_app.config["COVER_DIR"]
    cover_filename = f"comic_{comic.id}_cover.jpg"
    cover_path = os.path.join(cover_dir, cover_filename)

    if os.path.exists(cover_path):
        return cover_path

    image_data = None

    if chapter_data["type"] == "cbz":
        image_data = _extract_first_image_from_cbz(chapter_data["path"])
    elif chapter_data["type"] == "epub":
        image_data = _extract_cover_from_epub(chapter_data["path"])
    elif chapter_data["type"] == "folder":
        image_data = _extract_first_image_from_folder(chapter_data["path"])

    if image_data:
        try:
            img = Image.open(io.BytesIO(image_data))
            img = img.convert("RGB")
            img.thumbnail((400, 600))
            img.save(cover_path, "JPEG", quality=85)
            return cover_path
        except Exception:
            return None

    return None


def extract_page_image(page_path):
    if page_path.count("!") == 1:
        archive_path, inner_path = page_path.split("!", 1)
        ext = Path(archive_path).suffix.lower()

        if ext == ".epub":
            try:
                with zipfile.ZipFile(archive_path, "r") as zf:
                    return zf.read(inner_path)
            except (zipfile.BadZipFile, KeyError):
                return None
        else:
            try:
                with zipfile.ZipFile(archive_path, "r") as zf:
                    return zf.read(inner_path)
            except (zipfile.BadZipFile, KeyError):
                return None
    else:
        if os.path.isfile(page_path):
            with open(page_path, "rb") as f:
                return f.read()

    return None


def _extract_first_image_from_cbz(cbz_path):
    try:
        with zipfile.ZipFile(cbz_path, "r") as zf:
            image_names = sorted(
                n for n in zf.namelist()
                if not n.startswith("__MACOSX") and Path(n).suffix.lower() in IMAGE_EXTENSIONS
            )
            if image_names:
                return zf.read(image_names[0])
    except (zipfile.BadZipFile, KeyError):
        pass
    return None


def _extract_cover_from_epub(epub_path):
    try:
        pages = parse_epub_page_order(epub_path)
        if pages:
            cover_href = pages[0][0]
            with zipfile.ZipFile(epub_path, "r") as zf:
                try:
                    cover_data = zf.read(cover_href)
                    return cover_data
                except KeyError:
                    all_names = zf.namelist()
                    for name in sorted(all_names):
                        if (Path(name).suffix.lower() in IMAGE_EXTENSIONS
                                and not name.startswith("__MACOSX")):
                            return zf.read(name)
    except (zipfile.BadZipFile, Exception):
        pass
    return None


def _extract_first_image_from_folder(folder_path):
    images = sorted(
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
        and Path(f).suffix.lower() in IMAGE_EXTENSIONS
    )
    if images:
        with open(os.path.join(folder_path, images[0]), "rb") as f:
            return f.read()
    return None