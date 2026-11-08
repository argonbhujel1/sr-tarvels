"""
File uploads for local + Vercel.

Priority:
1. Cloudinary (required on Vercel / production)
2. /tmp (serverless writable dir)
3. app/static/uploads (local dev only)
"""
import os
import uuid
import tempfile
from flask import current_app


ALLOWED_DOC_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "webp", "doc", "docx"}
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif", "svg", "ico"}


def allowed_file(filename: str, allowed: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def _cloudinary_configured() -> bool:
    return bool(
        current_app.config.get("CLOUDINARY_CLOUD_NAME")
        and current_app.config.get("CLOUDINARY_API_KEY")
        and current_app.config.get("CLOUDINARY_API_SECRET")
    )


def _upload_cloudinary(file_storage, subfolder: str) -> str | None:
    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
            api_key=current_app.config["CLOUDINARY_API_KEY"],
            api_secret=current_app.config["CLOUDINARY_API_SECRET"],
            secure=True,
        )
        try:
            file_storage.stream.seek(0)
        except Exception:
            pass
        result = cloudinary.uploader.upload(
            file_storage,
            folder=f"sr-all-service/{subfolder}",
            resource_type="auto",
        )
        return result.get("secure_url") or result.get("url")
    except Exception as e:
        try:
            current_app.logger.warning("Cloudinary upload failed: %s", e)
        except Exception:
            print("Cloudinary upload failed:", e)
        return None


def _writable_dir(subfolder: str) -> str:
    tmp_base = os.environ.get("TMPDIR") or tempfile.gettempdir() or "/tmp"
    candidates = [
        os.path.join(tmp_base, "sr_uploads", subfolder),
        os.path.join(current_app.root_path, "static", "uploads", subfolder),
    ]
    for folder in candidates:
        try:
            os.makedirs(folder, exist_ok=True)
            test = os.path.join(folder, ".write_test")
            with open(test, "w") as f:
                f.write("1")
            os.remove(test)
            return folder
        except OSError:
            continue
    raise OSError(
        "No writable upload directory. Set Cloudinary env vars on Vercel: "
        "CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET"
    )


def save_local_upload(file_storage, subfolder: str = "docs") -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename, ALLOWED_DOC_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS):
        return None

    if _cloudinary_configured():
        url = _upload_cloudinary(file_storage, subfolder)
        if url:
            return url

    try:
        file_storage.stream.seek(0)
    except Exception:
        pass
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex[:12]}.{ext}"
    folder = _writable_dir(subfolder)
    path = os.path.join(folder, name)
    file_storage.save(path)

    if "static/uploads" in path.replace("\\", "/"):
        return f"/static/uploads/{subfolder}/{name}"
    return path
