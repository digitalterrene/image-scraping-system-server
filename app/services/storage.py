"""Safe local filesystem storage for scraped images."""

from __future__ import annotations

import re
from pathlib import Path

import aiofiles

_UNSAFE_FILENAME_CHARS = re.compile(r"[^a-zA-Z0-9._-]")
_MULTIPLE_DOTS = re.compile(r"\.{2,}")


class InvalidFilenameError(ValueError):
    """Raised when a filename fails validation or attempts path traversal."""


class ImageStorage:
    """Manages reading, writing, searching, and deleting image files safely."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir.resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_filename(raw_name: str, fallback_stem: str = "image", fallback_ext: str = ".img") -> str:
        """Sanitize an untrusted filename into a safe single-segment file name."""
        # Strip any directory components
        basename = Path(raw_name).name
        cleaned = _UNSAFE_FILENAME_CHARS.sub("_", basename)
        cleaned = _MULTIPLE_DOTS.sub(".", cleaned).strip("._")

        if not cleaned:
            ext = fallback_ext if fallback_ext.startswith(".") else f".{fallback_ext}"
            return f"{fallback_stem}{ext}"

        if "." not in cleaned and fallback_ext:
            ext = fallback_ext if fallback_ext.startswith(".") else f".{fallback_ext}"
            cleaned = f"{cleaned}{ext}"

        # Keep filenames within portable OS limits
        if len(cleaned) > 180:
            stem = Path(cleaned).stem[:150]
            suffix = Path(cleaned).suffix[:20]
            cleaned = f"{stem}{suffix}"

        return cleaned

    def resolve_safe_path(self, filename: str) -> Path:
        """Resolve a filename strictly within `base_dir`, preventing path traversal."""
        if not filename or "/" in filename or "\\" in filename or "\x00" in filename:
            raise InvalidFilenameError("Invalid filename.")

        if filename in {".", ".."} or filename.startswith("."):
            raise InvalidFilenameError("Invalid filename.")

        candidate = (self.base_dir / filename).resolve()
        if candidate.parent != self.base_dir:
            raise InvalidFilenameError("Path traversal attempt detected.")

        return candidate

    async def save_bytes(self, filename: str, data: bytes) -> Path:
        """Asynchronously write image bytes to storage."""
        safe_name = self.sanitize_filename(filename)
        target_path = self.resolve_safe_path(safe_name)
        async with aiofiles.open(target_path, "wb") as file_obj:
            await file_obj.write(data)
        return target_path

    def list_images(self, query: str | None = None) -> list[Path]:
        """Return stored image paths sorted alphabetically, optionally filtered by query."""
        if not self.base_dir.exists():
            return []

        normalized_query = query.strip().lower() if query else None
        files = [
            entry
            for entry in sorted(self.base_dir.iterdir(), key=lambda p: p.name.lower())
            if entry.is_file() and not entry.name.startswith(".")
        ]

        if normalized_query:
            return [entry for entry in files if normalized_query in entry.name.lower()]
        return files

    def get_image_path(self, filename: str) -> Path | None:
        """Return the resolved path if the file exists in storage, else None."""
        path = self.resolve_safe_path(filename)
        if path.exists() and path.is_file():
            return path
        return None

    def delete_image(self, filename: str) -> bool:
        """Delete a stored image file. Returns True if deleted, False if not found."""
        path = self.resolve_safe_path(filename)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False

    def count_images(self) -> int:
        """Return total number of stored image files."""
        return len(self.list_images())
