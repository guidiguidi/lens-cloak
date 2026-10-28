import os
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lens_cloak import LensCloaker
from strip_metadata import strip_image_metadata


def create_sample_image(path: Path):
    """Creates a simple RGB test image with mock EXIF tags."""
    img = Image.new("RGB", (100, 100), color=(128, 64, 200))
    exif = img.getexif()
    exif[0x010E] = "Test Image Description"
    exif[0x010F] = "Test Camera Make"
    img.save(path, "JPEG", exif=exif)


class TestLensCloak(unittest.TestCase):

    def test_strip_image_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "source.jpg"
            output_file = Path(tmpdir) / "clean.jpg"

            create_sample_image(input_file)

            with Image.open(input_file) as src:
                self.assertTrue(bool(src.getexif()))

            stats = strip_image_metadata(input_file, output_file)
            self.assertTrue(stats["had_exif"])
            self.assertTrue(output_file.exists())

            with Image.open(output_file) as cleaned:
                self.assertEqual(len(cleaned.getexif()), 0)

    def test_lens_cloaker_transformation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.png"
            output_file = Path(tmpdir) / "cloaked.png"

            arr = np.zeros((120, 120, 3), dtype=np.uint8)
            arr[:, :, 0] = np.linspace(0, 255, 120)
            arr[:, :, 1] = np.linspace(255, 0, 120)
            img = Image.fromarray(arr)
            img.save(input_file, "PNG")

            cloaker = LensCloaker(
                noise_intensity=4.0,
                rotate_deg=1.5,
                scale_factor=0.98,
                color_shift=2,
                jpeg_quality=95,
            )
            cloaker.flip_horizontal = True

            result = cloaker.process_image(input_file, output_file)
            self.assertTrue(result["metadata_stripped"])
            self.assertTrue(output_file.exists())

            with Image.open(output_file) as res:
                res_arr = np.array(res)
                self.assertEqual(res_arr.shape, (120, 120, 3))
                self.assertFalse(np.array_equal(arr, res_arr))


if __name__ == "__main__":
    unittest.main()
