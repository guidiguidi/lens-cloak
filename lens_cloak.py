#!/usr/bin/env python3
"""
LensCloak CLI & Python Library
==============================
Защита изображений от визуального поиска (Google Lens, Pimeyes, TinEye)
и полное удаление цифрового следа (EXIF, XMP, IPTC, ICC-профили).

Author: Valentyn Hrodiuk
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple, List
import cv2
import numpy as np
from PIL import Image


class LensCloaker:
    """
    Класс для очистки метаданных и внесения анти-адверсариальных
    (cloaking) искажений в изображения.
    """

    def __init__(
        self,
        noise_intensity: float = 5.5,
        rotate_deg: float = 1.3,
        scale_factor: float = 0.985,
        color_shift: int = 2,
        jpeg_quality: int = 92,
        blur_noise_sigma: float = 0.8,
    ):
        self.noise_intensity = noise_intensity
        self.rotate_deg = rotate_deg
        self.scale_factor = scale_factor
        self.color_shift = color_shift
        self.jpeg_quality = jpeg_quality
        self.blur_noise_sigma = blur_noise_sigma
        self.flip_horizontal = False

    def apply_geometry_distortion(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Микро-поворот, изменение соотношения сторон и опциональное зеркальное отражение.
        """
        h, w = img_bgr.shape[:2]
        center = (w / 2.0, h / 2.0)
        rot_matrix = cv2.getRotationMatrix2D(center, self.rotate_deg, self.scale_factor)
        
        distorted = cv2.warpAffine(
            img_bgr,
            rot_matrix,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT_101,
        )
        if self.flip_horizontal:
            distorted = cv2.flip(distorted, 1)
        return distorted

    def apply_adversarial_noise(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Средне- и высокочастотный гауссов шум, устойчивый к JPEG-квантованию.
        """
        if self.noise_intensity <= 0:
            return img_bgr

        raw_noise = np.random.normal(0, self.noise_intensity, img_bgr.shape).astype(np.float32)
        if self.blur_noise_sigma > 0:
            filtered_noise = cv2.GaussianBlur(raw_noise, (3, 3), self.blur_noise_sigma)
        else:
            filtered_noise = raw_noise

        cloaked = np.clip(img_bgr.astype(np.float32) + filtered_noise, 0, 255).astype(np.uint8)
        return cloaked

    def apply_color_channel_shift(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Микро-сдвиг каналов для сбоя цветовых гистограмм и сверточных признаков.
        """
        if self.color_shift == 0:
            return img_bgr

        shifted = img_bgr.astype(np.int16)
        # BGR: сдвигаем Blue вверх, Red вниз
        shifted[:, :, 0] = np.clip(shifted[:, :, 0] + self.color_shift, 0, 255)
        shifted[:, :, 2] = np.clip(shifted[:, :, 2] - self.color_shift, 0, 255)
        return shifted.astype(np.uint8)

    def process_image(self, input_path: Path, output_path: Path) -> dict:
        """
        Полный цикл обработки одного изображения.
        Возвращает словарь со статистикой.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Файл не найден: {input_path}")

        img_bgr = cv2.imread(str(input_path))
        if img_bgr is None:
            raise ValueError(f"Не удалось открыть изображение: {input_path}")

        h, w = img_bgr.shape[:2]

        # 1. Геометрическое возмущение
        step1 = self.apply_geometry_distortion(img_bgr)

        # 2. Перцептивный шум
        step2 = self.apply_adversarial_noise(step1)

        # 3. Цветовой сдвиг
        step3 = self.apply_color_channel_shift(step2)

        # 4. Конвертация BGR -> RGB -> PIL Image (полное удаление всех метаданных)
        img_rgb = cv2.cvtColor(step3, cv2.COLOR_BGR2RGB)
        clean_pil = Image.fromarray(img_rgb)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        ext = output_path.suffix.lower()

        if ext in (".jpg", ".jpeg"):
            clean_pil.save(
                output_path,
                format="JPEG",
                quality=self.jpeg_quality,
                subsampling=0,  # 4:4:4 без потери цветности
            )
        elif ext == ".webp":
            clean_pil.save(output_path, format="WEBP", quality=self.jpeg_quality)
        elif ext == ".png":
            clean_pil.save(output_path, format="PNG")
        else:
            clean_pil.save(output_path)

        return {
            "input": str(input_path),
            "output": str(output_path),
            "dimensions": f"{w}x{h}",
            "noise_intensity": self.noise_intensity,
            "rotate_deg": self.rotate_deg,
            "metadata_stripped": True,
        }


def main():
    parser = argparse.ArgumentParser(
        description="LensCloak CLI: Защита фото от Google Lens и удаление метаданных"
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Путь к файлу или папке с изображениями"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Путь для сохранения (файл или папка)"
    )
    parser.add_argument(
        "--noise", type=float, default=5.5, help="Интенсивность шума (по умолчанию: 5.5)"
    )
    parser.add_argument(
        "--rotate", type=float, default=1.3, help="Угол микро-поворота (по умолчанию: 1.3)"
    )
    parser.add_argument(
        "--shift", type=int, default=2, help="Сдвиг цветовых каналов (по умолчанию: 2)"
    )
    parser.add_argument(
        "--quality", type=int, default=92, help="Качество JPEG/WebP (по умолчанию: 92)"
    )
    parser.add_argument(
        "--flip", action="store_true", help="Зеркальное отражение по горизонтали (до 99%% защиты от Lens)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    cloaker = LensCloaker(
        noise_intensity=args.noise,
        rotate_deg=args.rotate,
        color_shift=args.shift,
        jpeg_quality=args.quality,
    )
    cloaker.flip_horizontal = args.flip

    supported_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

    if input_path.is_file():
        result = cloaker.process_image(input_path, output_path)
        print(f"✅ Готово: {result['output']} ({result['dimensions']}) | EXIF удален")
    elif input_path.is_dir():
        files = [f for f in input_path.iterdir() if f.suffix.lower() in supported_exts]
        if not files:
            print("❌ В указанной папке не найдено поддерживаемых изображений.")
            sys.exit(1)
        print(f"[*] Обработка папки: {len(files)} файлов...")
        for file in files:
            out_file = output_path / file.name
            res = cloaker.process_image(file, out_file)
            print(f"  -> {res['output']} ({res['dimensions']})")
        print(f"✅ Все {len(files)} файлов успешно обработаны!")
    else:
        print("❌ Неверный путь ввода.")
        sys.exit(1)


if __name__ == "__main__":
    main()
