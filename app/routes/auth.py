from flask import Blueprint, render_template, redirect, url_for, request, session, flash, g, jsonify, current_app
from app.models import db, User, ServerConfig, Library, Page, Chapter, Comic
from app.services.scanner import scan_library
import os

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/reset")
def reset_setup():
    if not current_app.debug:
        return "", 404
    for table in [Page, Chapter, Comic, Library, User, ServerConfig]:
        table.__table__.drop(db.engine, checkfirst=True)
    db.create_all()
    session.clear()
    return redirect(url_for("auth.setup"))


@auth_bp.route("/setup", methods=["GET", "POST"])
def setup():
    if ServerConfig.is_setup_done() and not session.get("setup_in_progress"):
        return redirect(url_for("pages.index"))

    current_step = session.get("setup_step", 1)

    if request.method == "POST":
        step = request.form.get("step", "")

        if step == "1":
            server_name = request.form.get("server_name", "Komiko").strip() or "Komiko"
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if not username or not password:
                flash("Username and password are required.", "error")
                return render_template("setup.html", step=1)

            if len(password) < 4:
                flash("Password must be at least 4 characters.", "error")
                return render_template("setup.html", step=1)

            if User.query.filter_by(username=username).first():
                flash("Username already taken.", "error")
                return render_template("setup.html", step=1)

            admin = User(username=username, is_admin=True)
            admin.set_password(password)
            db.session.add(admin)

            ServerConfig.set("server_name", server_name)
            ServerConfig.set("admin_created", "true")
            db.session.commit()

            session["user_id"] = admin.id
            session["setup_in_progress"] = True
            session["setup_step"] = 2
            return render_template("setup.html", step=2)

        elif step == "2":
            lib_name = request.form.get("lib_name", "").strip()
            lib_path = request.form.get("lib_path", "").strip()
            lib_type = request.form.get("lib_type", "manga")

            if lib_name and lib_path:
                if os.path.isdir(lib_path):
                    library = Library(
                        name=lib_name,
                        path=os.path.normpath(lib_path),
                        library_type=lib_type,
                    )
                    db.session.add(library)
                    db.session.commit()
                    scan_library(library.id)

            session["setup_step"] = 3
            return render_template("setup.html", step=3)

        elif step == "3":
            add_username = request.form.get("add_username", "").strip()
            add_password = request.form.get("add_password", "")

            if add_username and add_password:
                if not User.query.filter_by(username=add_username).first():
                    new_user = User(username=add_username, is_admin=False)
                    new_user.set_password(add_password)
                    db.session.add(new_user)
                    db.session.commit()

            session.pop("setup_in_progress", None)
            session.pop("setup_step", None)
            return redirect(url_for("pages.index"))

    return render_template("setup.html", step=current_step)


@auth_bp.route("/setup/validate-path", methods=["POST"])
def validate_path():
    path = request.form.get("path", "").strip()
    exists = os.path.isdir(path) if path else False
    return jsonify({"valid": exists, "path": os.path.normpath(path) if path else ""})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if not ServerConfig.is_setup_done():
        return redirect(url_for("auth.setup"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("pages.index"))

        flash("Invalid username or password.", "error")
        return render_template("login.html")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("auth.login"))


@auth_bp.route("/admin")
def admin():
    user = g.user
    if not user or not user.is_admin:
        return redirect(url_for("pages.index"))
    users = User.query.all()
    libraries = Library.query.all()
    return render_template("admin.html", users=users, libraries=libraries)


@auth_bp.route("/admin/users", methods=["POST"])
def create_user():
    user = g.user
    if not user or not user.is_admin:
        return redirect(url_for("pages.index"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    is_admin = request.form.get("is_admin") == "1"

    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect(url_for("auth.admin"))

    if User.query.filter_by(username=username).first():
        flash("Username already taken.", "error")
        return redirect(url_for("auth.admin"))

    new_user = User(username=username, is_admin=is_admin)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for("auth.admin"))


@auth_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    current = g.user
    if not current or not current.is_admin:
        return redirect(url_for("pages.index"))

    user = User.query.get_or_404(user_id)
    if user.id == current.id:
        flash("Cannot delete yourself.", "error")
        return redirect(url_for("auth.admin"))

    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("auth.admin"))


@auth_bp.route("/admin/settings", methods=["POST"])
def update_settings():
    user = g.user
    if not user or not user.is_admin:
        return redirect(url_for("pages.index"))

    server_name = request.form.get("server_name", "Komiko").strip() or "Komiko"
    ServerConfig.set("server_name", server_name)
    db.session.commit()

    return redirect(url_for("auth.admin"))