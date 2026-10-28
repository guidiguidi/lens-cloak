#!/usr/bin/env python3
"""
ClipboardCloak — Мгновенная защита фото прямо из буфера обмена macOS / Windows
=============================================================================
1. Сделайте скриншот или скопируйте картинку (Cmd+C / Ctrl+C).
2. Запустите `python3 clipboard_cloak.py`
3. Скрипт очистит метаданные, наложит cloaking-искажения и сохранит готовое фото.
"""

import sys
from pathlib import Path
from PIL import ImageGrab, Image
import numpy as np
import cv2


def main():
    print("📋 Чтение изображения из буфера обмена...")
    img = ImageGrab.grabclipboard()

    if img is None:
        print("❌ В буфере обмена нет изображения! Скопируйте фото (Cmd+C) или скриншот и повторите попытку.")
        sys.exit(1)

    if isinstance(img, list):
        # Если в буфер был скопирован путь к файлу
        file_path = Path(img[0])
        if file_path.exists():
            img = Image.open(file_path)
        else:
            print("❌ Файл из буфера обмена не найден.")
            sys.exit(1)

    # Приводим к RGB
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Перевод в OpenCV BGR
    img_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    h, w = img_bgr.shape[:2]

    # Микро-поворот на 1.2 градуса
    rot_matrix = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), 1.2, 0.985)
    distorted = cv2.warpAffine(img_bgr, rot_matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

    # Добавляем шум и цветовой сдвиг
    noise = np.random.normal(0, 5.5, distorted.shape).astype(np.float32)
    cloaked_bgr = np.clip(distorted.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    # Перевод в чистое PIL-изображение без метаданных
    clean_pil = Image.fromarray(cv2.cvtColor(cloaked_bgr, cv2.COLOR_BGR2RGB))

    output_path = Path("clipboard_cloaked_clean.png")
    clean_pil.save(output_path, format="PNG")

    print(f"✅ Готово! Изображение из буфера обработано, очищено от EXIF и сохранено в:")
    print(f"   👉 {output_path.resolve()}")


if __name__ == "__main__":
    main()
