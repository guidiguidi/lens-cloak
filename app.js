/**
 * LensCloak Studio — Client-Side Cloaking & Metadata Stripper Engine
 * ====================================================================
 * Обработка полностью происходит в браузере через HTML5 Canvas API.
 * Сохранение через canvas.toBlob() гарантирует 100% отсутствие EXIF/ICC/XMP.
 */

class LensCloakClientEngine {
    constructor() {
        this.originalImage = null;
        this.fileName = "image.jpg";
        this.currentView = "split"; // 'split' | 'diff'

        // UI References
        this.dropZone = document.getElementById("dropZone");
        this.fileInput = document.getElementById("fileInput");
        this.noiseSlider = document.getElementById("noiseIntensity");
        this.noiseVal = document.getElementById("noiseVal");
        this.rotationSlider = document.getElementById("rotationDeg");
        this.rotateVal = document.getElementById("rotateVal");
        this.colorSlider = document.getElementById("colorShift");
        this.colorVal = document.getElementById("colorVal");
        this.exportFormat = document.getElementById("exportFormat");
        this.downloadBtn = document.getElementById("downloadBtn");
        this.copyBtn = document.getElementById("copyBtn");
        this.flipCheckbox = document.getElementById("flipHorizontal");

        // Canvases
        this.origCanvas = document.getElementById("origCanvas");
        this.cloakedCanvas = document.getElementById("cloakedCanvas");
        this.diffCanvas = document.getElementById("diffCanvas");
        this.ctxOrig = this.origCanvas.getContext("2d", { willReadFrequently: true });
        this.ctxCloak = this.cloakedCanvas.getContext("2d", { willReadFrequently: true });
        this.ctxDiff = this.diffCanvas.getContext("2d");

        this.initEventListeners();
    }

    initEventListeners() {
        // Global Paste (Cmd+V / Ctrl+V)
        window.addEventListener("paste", (e) => {
            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
            for (let item of items) {
                if (item.type.indexOf("image") === 0) {
                    const blob = item.getAsFile();
                    this.loadImage(blob, "pasted_from_clipboard.png");
                    break;
                }
            }
        });

        // Drag & Drop
        this.dropZone.addEventListener("click", () => this.fileInput.click());
        this.dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            this.dropZone.classList.add("dragover");
        });
        this.dropZone.addEventListener("dragleave", () => {
            this.dropZone.classList.remove("dragover");
        });
        this.dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            this.dropZone.classList.remove("dragover");
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                this.loadImage(e.dataTransfer.files[0]);
            }
        });

        this.folderInput = document.getElementById("folderInput");
        this.folderSelectBtn = document.getElementById("folderSelectBtn");

        this.fileInput.addEventListener("change", (e) => {
            if (e.target.files && e.target.files[0]) {
                this.loadImage(e.target.files[0]);
            }
        });

        if (this.folderSelectBtn && this.folderInput) {
            this.folderSelectBtn.addEventListener("click", () => this.folderInput.click());
            this.folderInput.addEventListener("change", (e) => {
                const files = Array.from(e.target.files).filter((f) => f.type.startsWith("image/"));
                if (files.length === 0) {
                    alert("В выбранной папке не найдено изображений.");
                    return;
                }
                alert(`Выбрана папка с ${files.length} фото. Будет загружено первое изображение для предпросмотра. При нажатии «Скачать» обработанное фото экспортируется без метаданных.`);
                this.loadImage(files[0]);
            });
        }

        // Sliders live update
        const handleSliderChange = () => {
            this.noiseVal.textContent = parseFloat(this.noiseSlider.value).toFixed(1);
            this.rotateVal.textContent = `${parseFloat(this.rotationSlider.value).toFixed(1)}°`;
            this.colorVal.textContent = `${this.colorSlider.value} px`;
            if (this.originalImage) {
                this.processAndRender();
            }
        };

        this.noiseSlider.addEventListener("input", handleSliderChange);
        this.rotationSlider.addEventListener("input", handleSliderChange);
        this.colorSlider.addEventListener("input", handleSliderChange);
        if (this.flipCheckbox) {
            this.flipCheckbox.addEventListener("change", handleSliderChange);
        }

        // View Tabs
        document.querySelectorAll(".tab-btn").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
                e.target.classList.add("active");
                this.currentView = e.target.dataset.view;
                this.updateViewVisibility();
            });
        });

        // Download & Copy Actions
        this.downloadBtn.addEventListener("click", () => this.exportCloakedImage());
        if (this.copyBtn) {
            this.copyBtn.addEventListener("click", () => this.copyCloakedToClipboard());
        }
    }

    updateViewVisibility() {
        const sideBySide = document.getElementById("sideBySide");
        const diffView = document.getElementById("diffView");

        if (!this.originalImage) return;

        if (this.currentView === "split") {
            sideBySide.style.display = "grid";
            diffView.style.display = "none";
        } else {
            sideBySide.style.display = "none";
            diffView.style.display = "flex";
        }
    }

    loadImage(file, customName = null) {
        if (!file.type.startsWith("image/")) {
            alert("Пожалуйста, выберите файл изображения (JPG, PNG, WebP).");
            return;
        }

        this.fileName = customName || file.name || "pasted_image.png";
        const reader = new FileReader();

        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                this.originalImage = img;
                this.onImageLoaded();
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    onImageLoaded() {
        document.getElementById("placeholderMsg").style.display = "none";
        document.getElementById("statusBar").style.display = "flex";
        document.getElementById("fileInfo").textContent = `${this.fileName} (${this.originalImage.width}×${this.originalImage.height})`;
        document.getElementById("statusDims").textContent = `${this.originalImage.width} × ${this.originalImage.height}`;
        this.downloadBtn.disabled = false;
        if (this.copyBtn) this.copyBtn.disabled = false;

        this.updateViewVisibility();
        this.processAndRender();
    }

    processAndRender() {
        const w = this.originalImage.width;
        const h = this.originalImage.height;

        // Set canvas dimensions
        [this.origCanvas, this.cloakedCanvas, this.diffCanvas].forEach((c) => {
            c.width = w;
            c.height = h;
        });

        // 1. Draw original
        this.ctxOrig.clearRect(0, 0, w, h);
        this.ctxOrig.drawImage(this.originalImage, 0, 0, w, h);

        // 2. Compute cloaking transformations on cloakedCanvas
        const angleDeg = parseFloat(this.rotationSlider.value);
        const scale = 0.985;

        this.ctxCloak.clearRect(0, 0, w, h);
        this.ctxCloak.save();
        this.ctxCloak.translate(w / 2, h / 2);
        this.ctxCloak.rotate((angleDeg * Math.PI) / 180);
        const flipX = (this.flipCheckbox && this.flipCheckbox.checked) ? -1 : 1;
        this.ctxCloak.scale(scale * flipX, scale);
        this.ctxCloak.drawImage(this.originalImage, -w / 2, -h / 2, w, h);
        this.ctxCloak.restore();

        // 3. Pixel manipulation: Adversarial Noise + Color Shift
        const noiseIntensity = parseFloat(this.noiseSlider.value);
        const colorShift = parseInt(this.colorSlider.value, 10);

        const imgData = this.ctxCloak.getImageData(0, 0, w, h);
        const origData = this.ctxOrig.getImageData(0, 0, w, h);
        const diffData = this.ctxDiff.createImageData(w, h);

        const data = imgData.data;
        const origPixels = origData.data;
        const diffPixels = diffData.data;

        for (let i = 0; i < data.length; i += 4) {
            // Generate adversarial gaussian-like noise
            const u1 = Math.random() || 1e-6;
            const u2 = Math.random() || 1e-6;
            const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
            const noise = z0 * noiseIntensity;

            // Apply color shift + noise
            const r = Math.min(255, Math.max(0, data[i] - colorShift + noise));
            const g = Math.min(255, Math.max(0, data[i + 1] + noise * 0.7));
            const b = Math.min(255, Math.max(0, data[i + 2] + colorShift + noise));

            data[i] = r;
            data[i + 1] = g;
            data[i + 2] = b;

            // Compute difference heatmap for inspection
            const dr = Math.abs(r - origPixels[i]);
            const dg = Math.abs(g - origPixels[i + 1]);
            const db = Math.abs(b - origPixels[i + 2]);

            // Amplify diff by 15x for clear visual feedback
            const diffIntensity = Math.min(255, (dr + dg + db) * 5);
            diffPixels[i] = diffIntensity;       // R (Purple-ish glow)
            diffPixels[i + 1] = diffIntensity * 0.3; // G
            diffPixels[i + 2] = 255;             // B
            diffPixels[i + 3] = 255;             // Alpha
        }

        this.ctxCloak.putImageData(imgData, 0, 0);
        this.ctxDiff.putImageData(diffData, 0, 0);
    }

    exportCloakedImage() {
        if (!this.originalImage) return;

        const mimeType = this.exportFormat.value;
        const quality = mimeType === "image/jpeg" || mimeType === "image/webp" ? 0.93 : undefined;

        this.cloakedCanvas.toBlob(
            (blob) => {
                if (!blob) return;
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                const baseName = this.fileName.replace(/\.[^/.]+$/, "");
                const ext = mimeType.split("/")[1];

                a.href = url;
                a.download = `${baseName}_CLOAKED_CLEAN.${ext}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            },
            mimeType,
            quality
        );
    }

    copyCloakedToClipboard() {
        if (!this.originalImage) return;

        this.cloakedCanvas.toBlob(async (blob) => {
            if (!blob) return;
            try {
                await navigator.clipboard.write([
                    new ClipboardItem({
                        [blob.type]: blob
                    })
                ]);
                const origText = this.copyBtn.innerHTML;
                this.copyBtn.innerHTML = "<span>✅ Скопировано! Можно вставлять (Cmd+V)</span>";
                setTimeout(() => {
                    this.copyBtn.innerHTML = origText;
                }, 2500);
            } catch (err) {
                console.error("Не удалось скопировать в буфер:", err);
                alert("Ошибка копирования: убедитесь, что браузер разрешает доступ к буферу обмена.");
            }
        }, "image/png");
    }
}

// Initialize on page load
window.addEventListener("DOMContentLoaded", () => {
    new LensCloakClientEngine();
});
