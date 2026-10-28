#!/usr/bin/env python3
"""
CleanMeta — 100% очистка всех метаданных папки с изображениями
============================================================
Выбор входной папки (Input Directory) и папки назначения (Output Directory).
Поддерживает как CLI-аргументы (-i /path/in -o /path/out),
так и интерактивные графические окна выбора папок (если запущено без аргументов).
"""

import argparse
import sys
from pathlib import Path
from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}


def strip_image_metadata(input_path: Path, output_path: Path, quality: int = 95) -> dict:
    """
    Удаляет все EXIF / GPS / XMP / ICC метаданные путем пересоздания
    чистого буфера пикселей в памяти.
    """
    with Image.open(input_path) as img:
        exif_present = bool(img.getexif() or img.info.get("exif"))
        xmp_present = "xmp" in img.info or "XML:com.adobe.xmp" in img.info
        icc_present = "icc_profile" in img.info

        if img.mode in ("P", "CMYK"):
            clean_img = img.convert("RGB")
        elif img.mode in ("RGBA", "LA"):
            clean_img = img.convert("RGBA")
        else:
            clean_img = img.convert("RGB")

        # Создаем новый холст без метаданных и копируем только пиксели
        pristine_img = Image.new(clean_img.mode, clean_img.size)
        pixel_data = (
            clean_img.get_flattened_data()
            if hasattr(clean_img, "get_flattened_data")
            else list(clean_img.getdata())
        )
        pristine_img.putdata(pixel_data)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        ext = output_path.suffix.lower()

        if ext in (".jpg", ".jpeg"):
            if pristine_img.mode != "RGB":
                pristine_img = pristine_img.convert("RGB")
            pristine_img.save(
                output_path,
                format="JPEG",
                quality=quality,
                subsampling=0,
                exif=b"",
            )
        elif ext == ".png":
            pristine_img.save(output_path, format="PNG")
        elif ext == ".webp":
            pristine_img.save(output_path, format="WEBP", quality=quality, exif=b"")
        else:
            pristine_img.save(output_path)

        return {
            "input": str(input_path),
            "output": str(output_path),
            "size": f"{clean_img.width}x{clean_img.height}",
            "had_exif": exif_present,
            "had_xmp": xmp_present,
            "had_icc": icc_present,
        }


def process_directory(input_dir: Path, output_dir: Path, quality: int = 95):
    """
    Пакетная обработка всех изображений из input_dir и сохранение в output_dir.
    """
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"❌ Ошибка: входная папка не найдена: {input_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    files = [f for f in sorted(input_dir.iterdir()) if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]
    if not files:
        print(f"❌ В папке {input_dir} не найдено поддерживаемых изображений.")
        sys.exit(1)

    print(f"\n📂 Входная папка : {input_dir}")
    print(f"📁 Папка выхода  : {output_dir}")
    print(f"[*] Найдено файлов: {len(files)}\n")

    cleaned_count = 0
    for idx, file_path in enumerate(files, 1):
        out_file = output_dir / file_path.name
        try:
            res = strip_image_metadata(file_path, out_file, quality=quality)
            meta_removed = []
            if res["had_exif"]:
                meta_removed.append("EXIF/GPS")
            if res["had_xmp"]:
                meta_removed.append("XMP")
            if res["had_icc"]:
                meta_removed.append("ICC")

            meta_str = f" [Удалено: {', '.join(meta_removed)}]" if meta_removed else " [Чистый]"
            print(f"  [{idx:02d}/{len(files):02d}] ✅ {file_path.name} -> {out_file.name} ({res['size']}){meta_str}")
            cleaned_count += 1
        except Exception as e:
            print(f"  [{idx:02d}/{len(files):02d}] ❌ Ошибка при обработке {file_path.name}: {e}")

    print(f"\n🎉 Успешно очищено {cleaned_count} из {len(files)} фотографий!")
    print(f"💾 Результат сохранен в директории: {output_dir.resolve()}\n")


def select_directories_gui():
    """
    Открывает системные диалоговые окна выбора папки ввода и папки вывода.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        print("🔍 Выберите входную папку с фотографиями в открывшемся окне...")
        in_dir = filedialog.askdirectory(title="Выберите папку с исходными изображениями (Input Folder)")
        if not in_dir:
            print("❌ Выбор входной папки отменен.")
            sys.exit(0)

        print("📁 Выберите папку для сохранения очищенных фотографий...")
        out_dir = filedialog.askdirectory(title="Выберите директорию для сохранения (Output Directory)")
        if not out_dir:
            print("❌ Выбор выходной папки отменен.")
            sys.exit(0)

        return Path(in_dir), Path(out_dir)
    except Exception as e:
        print(f"⚠️ Не удалось открыть графическое окно выбора папок: {e}")
        in_dir = input("Введите путь к входной папке (Input Directory): ").strip()
        out_dir = input("Введите путь к выходной директории (Output Directory): ").strip()
        return Path(in_dir), Path(out_dir)


def main():
    parser = argparse.ArgumentParser(
        description="CleanMeta: 100% очистка метаданных (EXIF, GPS, XMP, ICC) в папке"
    )
    parser.add_argument(
        "-i",
        "--input",
        required=False,
        help="Входная папка с изображениями (если не указана — откроется окно выбора)",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=False,
        help="Выходная директория для сохранения очищенных файлов",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=95,
        help="Качество JPEG/WebP при сохранении (по умолчанию: 95)",
    )

    args = parser.parse_args()

    if args.input and args.output:
        in_dir = Path(args.input)
        out_dir = Path(args.output)
    elif args.input and not args.output:
        in_dir = Path(args.input)
        out_dir = in_dir / "cleaned_output"
    else:
        in_dir, out_dir = select_directories_gui()

    process_directory(in_dir, out_dir, quality=args.quality)


if __name__ == "__main__":
    main()
