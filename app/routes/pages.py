from flask import Blueprint, render_template, send_from_directory
from app.models import Library, Comic, Chapter

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    libraries = Library.query.all()
    return render_template("libraries.html", libraries=libraries)


@pages_bp.route("/library/<int:library_id>")
def library(library_id):
    library = Library.query.get_or_404(library_id)
    comics = Comic.query.filter_by(library_id=library_id).order_by(Comic.title).all()
    return render_template("library.html", library=library, comics=comics)


@pages_bp.route("/comic/<int:comic_id>")
def comic(comic_id):
    comic = Comic.query.get_or_404(comic_id)
    chapters = Chapter.query.filter_by(comic_id=comic_id).order_by(Chapter.chapter_number).all()
    return render_template("comic.html", comic=comic, chapters=chapters)


@pages_bp.route("/reader/<int:chapter_id>")
def reader(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    comic = Comic.query.get_or_404(chapter.comic_id)
    chapters = Chapter.query.filter_by(comic_id=comic.id).order_by(Chapter.chapter_number).all()
    pages = chapter.pages.order_by("page_number").all()
    return render_template("reader.html", comic=comic, chapter=chapter, chapters=chapters, pages=pages)


@pages_bp.route("/covers/<path:filename>")
def cover(filename):
    from flask import current_app
    return send_from_directory(current_app.config["COVER_DIR"], filename)


@pages_bp.route("/page_image/<int:page_id>")
def page_image(page_id):
    from app.models import Page
    from app.services.comic_parser import extract_page_image
    from flask import Response

    page = Page.query.get_or_404(page_id)
    image_data = extract_page_image(page.file_path)
    if image_data:
        ext = "." + page.file_path.rsplit(".", 1)[-1].lower() if "." in page.file_path else ".jpg"

        content_type = "image/jpeg"
        if ext in (".png",):
            content_type = "image/png"
        elif ext in (".gif",):
            content_type = "image/gif"
        elif ext in (".webp",):
            content_type = "image/webp"

        return Response(image_data, content_type=content_type)
    return "", 404