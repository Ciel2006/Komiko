from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class ServerConfig(db.Model):
    __tablename__ = "server_config"

    key = db.Column(db.String(255), primary_key=True)
    value = db.Column(db.Text, nullable=True)

    @staticmethod
    def is_setup_done():
        row = ServerConfig.query.get("admin_created")
        return row is not None and row.value == "true"

    @staticmethod
    def get(key, default=None):
        row = ServerConfig.query.get(key)
        return row.value if row else default

    @staticmethod
    def set(key, value):
        row = ServerConfig.query.get(key)
        if row:
            row.value = value
        else:
            row = ServerConfig(key=key, value=value)
            db.session.add(row)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    bookmarks = db.relationship("Bookmark", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    reading_progress = db.relationship("ReadingProgress", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "is_admin": self.is_admin,
            "date_created": self.date_created.isoformat() if self.date_created else None,
        }


class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comic_id = db.Column(db.Integer, db.ForeignKey("comics.id"), nullable=False)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "comic_id"),)


class ReadingProgress(db.Model):
    __tablename__ = "reading_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comic_id = db.Column(db.Integer, db.ForeignKey("comics.id"), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapters.id"), nullable=True)
    last_page = db.Column(db.Integer, default=0)
    date_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "comic_id"),)

    chapter = db.relationship("Chapter")

    __table_args__ = (db.UniqueConstraint("user_id", "comic_id"),)


class Library(db.Model):
    __tablename__ = "libraries"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(1024), nullable=False)
    library_type = db.Column(db.String(50), nullable=False, default="manga")
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    comics = db.relationship("Comic", backref="library", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "library_type": self.library_type,
            "date_added": self.date_added.isoformat() if self.date_added else None,
            "comic_count": self.comics.count(),
        }


class Comic(db.Model):
    __tablename__ = "comics"

    id = db.Column(db.Integer, primary_key=True)
    library_id = db.Column(db.Integer, db.ForeignKey("libraries.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    folder_path = db.Column(db.String(1024), nullable=False)
    cover_path = db.Column(db.String(1024), nullable=True)
    description = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    chapters = db.relationship("Chapter", backref="comic", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "library_id": self.library_id,
            "title": self.title,
            "cover_path": self.cover_path,
            "description": self.description,
            "chapter_count": self.chapters.count(),
            "date_added": self.date_added.isoformat() if self.date_added else None,
        }


class Chapter(db.Model):
    __tablename__ = "chapters"

    id = db.Column(db.Integer, primary_key=True)
    comic_id = db.Column(db.Integer, db.ForeignKey("comics.id"), nullable=False)
    chapter_number = db.Column(db.Float, nullable=False)
    title = db.Column(db.String(255), nullable=True)
    folder_path = db.Column(db.String(1024), nullable=False)
    page_count = db.Column(db.Integer, default=0)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    pages = db.relationship("Page", backref="chapter", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "comic_id": self.comic_id,
            "chapter_number": self.chapter_number,
            "title": self.title,
            "page_count": self.page_count,
            "date_added": self.date_added.isoformat() if self.date_added else None,
        }


class Page(db.Model):
    __tablename__ = "pages"

    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapters.id"), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(1024), nullable=False)