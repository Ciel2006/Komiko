from flask import Blueprint, jsonify, request
from app.models import db, Library, Comic
from app.services.scanner import scan_library

libraries_bp = Blueprint("libraries", __name__)


@libraries_bp.route("", methods=["GET"])
def list_libraries():
    libraries = Library.query.all()
    return jsonify([lib.to_dict() for lib in libraries])


@libraries_bp.route("", methods=["POST"])
def create_library():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("path"):
        return jsonify({"error": "name and path are required"}), 400

    import os
    if not os.path.isdir(data["path"]):
        return jsonify({"error": "path does not exist or is not a directory"}), 400

    library = Library(
        name=data["name"],
        path=os.path.normpath(data["path"]),
        library_type=data.get("library_type", "manga"),
    )
    db.session.add(library)
    db.session.commit()

    return jsonify(library.to_dict()), 201


@libraries_bp.route("/<int:library_id>", methods=["GET"])
def get_library(library_id):
    library = Library.query.get_or_404(library_id)
    return jsonify(library.to_dict())


@libraries_bp.route("/<int:library_id>", methods=["DELETE"])
def delete_library(library_id):
    library = Library.query.get_or_404(library_id)
    db.session.delete(library)
    db.session.commit()
    return jsonify({"deleted": True})


@libraries_bp.route("/<int:library_id>/scan", methods=["POST"])
def scan_library_endpoint(library_id):
    library, error = scan_library(library_id)
    if error:
        return jsonify({"error": error}), 400

    comics = Comic.query.filter_by(library_id=library_id).all()
    return jsonify({
        "library": library.to_dict(),
        "comics_found": len(comics),
    })