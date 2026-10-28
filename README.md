# lens-cloak

[![CI](https://github.com/guidiguidi/lens-cloak/actions/workflows/ci.yml/badge.svg)](https://github.com/guidiguidi/lens-cloak/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An adversarial perturbation and metadata elimination toolkit designed to shield images against reverse-image search and AI facial recognition crawlers (Google Lens, PimEyes, TinEye, Bing Visual Search) while preserving perceptual fidelity for human viewers.

Includes both a **Python CLI & engine** and a **zero-dependency client-side Web Canvas Studio**.

## Evasion Mechanisms

1. **Adversarial Noise Injection**:
   - Injects high/mid-frequency Gaussian perturbations calibrated to disrupt convolutional neural network (CNN) and Vision Transformer (ViT) embedding layers without degrading visual perception.
2. **Subtle Spatial & Geometry Warping**:
   - Micro-rotations (1.0°–1.5°) with seamless boundary reflection (`BORDER_REFLECT_101`) to break spatial coordinate alignment and perceptual hashing (pHash/dHash).
3. **Chromatic Channel Micro-Shift**:
   - Opposing R/B color channel displacement to distort machine vision color histogram clustering.
4. **100% Digital Footprint Sanitization**:
   - Pure pixel-buffer reconstruction in memory.
   - Eliminates EXIF tags, GPS geolocations, camera serials, ICC color profiles, and embedded thumbnail previews.

## Components

- **`lens_cloak.py`**: Batch & single-image adversarial processing pipeline using OpenCV and NumPy.
- **`strip_metadata.py`**: High-speed lossless EXIF, GPS, and XMP sanitization utility.
- **`clipboard_cloak.py`**: Instant clipboard hook (macOS / Windows) to sanitize and cloak screenshots in one keystroke.
- **`index.html` / `app.js`**: 100% in-browser HTML5 Canvas app with live slider preview.

## Quick Start

### Installation

```bash
git clone https://github.com/guidiguidi/lens-cloak.git
cd lens-cloak
pip install -r requirements.txt
```

### CLI Usage

**Cloak a single image:**
```bash
python lens_cloak.py -i photo.jpg -o cloaked.jpg --noise 5.5 --rotate 1.3 --flip
```

**Batch process an entire directory:**
```bash
python lens_cloak.py -i ./input_folder -o ./output_folder --noise 6.0
```

**Strip metadata only (lossless):**
```bash
python strip_metadata.py -i ./raw_photos -o ./clean_photos -q 95
```

### Running the Web Studio

Serve locally with Python or Docker:
```bash
python -m http.server 8000
# or
docker compose up -d
```
Open `http://localhost:8000` in your browser. All processing happens entirely client-side on the HTML5 Canvas.

## Testing

Run unit tests across test suites:
```bash
python -m unittest discover -s tests
# or
pytest -v tests/
```

## License

MIT
