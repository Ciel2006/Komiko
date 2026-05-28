from flask import Blueprint, render_template, send_from_directory, jsonify, redirect, url_for, g
from app.models import db, Library, Comic, Chapter, Bookmark, ReadingProgress

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    libraries = Library.query.all()

    from flask import g
    progress_data = {}
    bookmark_ids = set()
    if g.user:
        bookmark_ids = {b.comic_id for b in g.user.bookmarks.all()}
        for rp in g.user.reading_progress.all():
            progress_data[rp.comic_id] = {
                "chapter_id": rp.chapter_id,
                "chapter_number": rp.chapter.chapter_number if rp.chapter else None,
                "last_page": rp.last_page,
            }

    return render_template("libraries.html", libraries=libraries, bookmark_ids=bookmark_ids, progress_data=progress_data)


@pages_bp.route("/library/<int:library_id>")
def library(library_id):
    library = Library.query.get_or_404(library_id)
    comics = Comic.query.filter_by(library_id=library_id).order_by(Comic.title).all()

    from flask import g
    progress_data = {}
    bookmark_ids = set()
    if g.user:
        bookmark_ids = {b.comic_id for b in g.user.bookmarks.all()}
        for rp in g.user.reading_progress.all():
            progress_data[rp.comic_id] = {
                "chapter_id": rp.chapter_id,
                "chapter_number": rp.chapter.chapter_number if rp.chapter else None,
            }

    return render_template("library.html", library=library, comics=comics, bookmark_ids=bookmark_ids, progress_data=progress_data)


@pages_bp.route("/comic/<int:comic_id>")
def comic(comic_id):
    comic = Comic.query.get_or_404(comic_id)
    chapters = Chapter.query.filter_by(comic_id=comic_id).order_by(Chapter.chapter_number).all()

    from flask import g
    is_bookmarked = False
    progress = None
    new_chapters = 0

    if g.user:
        bm = Bookmark.query.filter_by(user_id=g.user.id, comic_id=comic_id).first()
        is_bookmarked = bm is not None

        rp = ReadingProgress.query.filter_by(user_id=g.user.id, comic_id=comic_id).first()
        if rp:
            progress = rp
            last_ch_num = rp.chapter.chapter_number if rp.chapter else 0
            new_chapters = Chapter.query.filter(
                Chapter.comic_id == comic_id,
                Chapter.chapter_number > last_ch_num
            ).count()

    return render_template("comic.html", comic=comic, chapters=chapters, is_bookmarked=is_bookmarked, progress=progress, new_chapters=new_chapters)


@pages_bp.route("/reader/<int:chapter_id>")
def reader(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    comic = Comic.query.get_or_404(chapter.comic_id)
    chapters = Chapter.query.filter_by(comic_id=comic.id).order_by(Chapter.chapter_number).all()
    pages = chapter.pages.order_by("page_number").all()

    from flask import g, session
    if g.user:
        rp = ReadingProgress.query.filter_by(user_id=g.user.id, comic_id=comic.id).first()
        if rp:
            rp.chapter_id = chapter.id
            rp.last_page = 0
        else:
            rp = ReadingProgress(user_id=g.user.id, comic_id=comic.id, chapter_id=chapter.id, last_page=0)
            db.session.add(rp)
        db.session.commit()

    return render_template("reader.html", comic=comic, chapter=chapter, chapters=chapters, pages=pages)


@pages_bp.route("/profile")
def profile():
    user = g.user
    if not user:
        return redirect(url_for("auth.login"))

    bookmark_count = user.bookmarks.count()
    progress_entries = user.reading_progress.all()

    comics_read = []
    for rp in progress_entries:
        comic = Comic.query.get(rp.comic_id)
        if comic:
            chapter = Chapter.query.get(rp.chapter_id) if rp.chapter_id else None
            total_chapters = comic.chapters.count()
            comics_read.append({
                "comic": comic,
                "progress": rp,
                "chapter": chapter,
                "total_chapters": total_chapters,
            })

    return render_template("profile.html", user=user, bookmark_count=bookmark_count, comics_read=comics_read)


@pages_bp.route("/bookmarks")
def bookmarks():
    user = g.user
    if not user:
        return redirect(url_for("auth.login"))

    bookmark_list = user.bookmarks.all()
    comics = []
    for bm in bookmark_list:
        comic = Comic.query.get(bm.comic_id)
        if comic:
            comics.append(comic)

    progress_data = {}
    if user:
        for rp in user.reading_progress.all():
            progress_data[rp.comic_id] = {
                "chapter_id": rp.chapter_id,
                "chapter_number": rp.chapter.chapter_number if rp.chapter else None,
            }

    return render_template("bookmarks.html", comics=comics, progress_data=progress_data)


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