"""Unit tests for the local image storage backend and path-traversal guards."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from app.services.storage import ImageStorage, InvalidFilenameError


class TestImageStorage(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.storage = ImageStorage(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_sanitize_filename_removes_unsafe_chars_and_paths(self) -> None:
        self.assertEqual(
            ImageStorage.sanitize_filename("../../evil/my photo (1).png"),
            "my_photo__1_.png",
        )
        self.assertEqual(
            ImageStorage.sanitize_filename("noext", fallback_ext=".jpg"),
            "noext.jpg",
        )
        self.assertEqual(
            ImageStorage.sanitize_filename("...", fallback_stem="img_1", fallback_ext=".png"),
            "img_1.png",
        )

    def test_resolve_safe_path_blocks_traversal(self) -> None:
        for bad_name in ["../secret.txt", "..\\secret.txt", ".hidden", "..", "a/b.png", "x\x00.png"]:
            with self.assertRaises(InvalidFilenameError, msg=f"Should reject {bad_name!r}"):
                self.storage.resolve_safe_path(bad_name)

    def test_save_list_search_get_and_delete(self) -> None:
        saved = asyncio.run(self.storage.save_bytes("sunset_beach.png", b"\x89PNG\r\n"))
        self.assertTrue(saved.exists())
        self.assertEqual(self.storage.count_images(), 1)

        all_files = self.storage.list_images()
        self.assertEqual([p.name for p in all_files], ["sunset_beach.png"])

        matched = self.storage.list_images(query="SUNSET")
        self.assertEqual([p.name for p in matched], ["sunset_beach.png"])

        unmatched = self.storage.list_images(query="mountain")
        self.assertEqual(unmatched, [])

        self.assertEqual(self.storage.get_image_path("sunset_beach.png"), saved)
        self.assertIsNone(self.storage.get_image_path("missing.png"))

        self.assertTrue(self.storage.delete_image("sunset_beach.png"))
        self.assertFalse(self.storage.delete_image("sunset_beach.png"))
        self.assertEqual(self.storage.count_images(), 0)


if __name__ == "__main__":
    unittest.main()
