import sys
import os
import io
import asyncio
import json
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, QLabel, QScrollArea, QGridLayout,
    QCheckBox, QFileDialog, QProgressBar, QDialog, QMessageBox, QFrame,
    QSplitter, QSpinBox, QSizePolicy, QCompleter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QRunnable, QThreadPool, QStringListModel
from PyQt6.QtGui import QPixmap, QImage, QIcon, QFont, QColor, QPalette, QCursor

from core.models import Post, SearchRequest
from core.providers.manager import ProviderManager
from core.downloader import DownloadManager
from core.tag_suggest import POPULAR_TAGS, suggest_tags
from core.settings import load_settings, save_settings

# Modern Dark Theme Stylesheet
DARK_STYLESHEET = """
QMainWindow, QWidget#CentralWidget {
    background-color: #0f111a;
    color: #e2e8f0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QFrame#HeaderFrame {
    background-color: #171925;
    border-bottom: 1px solid #2d3748;
    padding: 8px 16px;
}

QFrame#ToolbarFrame {
    background-color: #131622;
    border-bottom: 1px solid #232938;
    padding: 6px 16px;
}

QFrame#FooterFrame {
    background-color: #171925;
    border-top: 1px solid #2d3748;
    padding: 8px 16px;
}

QLabel {
    color: #cbd5e1;
}

QLabel#AppTitle {
    font-size: 18px;
    font-weight: bold;
    color: #ec4899;
}

QLabel#Badge {
    background-color: #2b2f45;
    color: #a5b4fc;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: bold;
}

QLineEdit {
    background-color: #1e2233;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    color: #f8fafc;
    font-size: 13px;
    selection-background-color: #ec4899;
}

QLineEdit:focus {
    border: 1px solid #ec4899;
    background-color: #24293e;
}

QComboBox {
    background-color: #1e2233;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 6px 12px;
    color: #f8fafc;
    min-width: 110px;
}

QComboBox:hover {
    border-color: #475569;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #1e2233;
    color: #f8fafc;
    selection-background-color: #ec4899;
    border: 1px solid #334155;
    outline: none;
}

QPushButton {
    background-color: #282e44;
    border: 1px solid #3b4461;
    border-radius: 8px;
    padding: 7px 16px;
    color: #f1f5f9;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #373f5c;
    border-color: #6366f1;
}

QPushButton:pressed {
    background-color: #1e2233;
}

QPushButton#PrimaryBtn {
    background-color: #ec4899;
    border: 1px solid #f472b6;
    color: #ffffff;
    font-weight: bold;
}

QPushButton#PrimaryBtn:hover {
    background-color: #db2777;
    border-color: #f472b6;
}

QPushButton#SuccessBtn {
    background-color: #10b981;
    border: 1px solid #34d399;
    color: #ffffff;
    font-weight: bold;
}

QPushButton#SuccessBtn:hover {
    background-color: #059669;
}

QPushButton#DangerBtn {
    background-color: #ef4444;
    border: 1px solid #f87171;
    color: #ffffff;
}

QPushButton#DangerBtn:hover {
    background-color: #dc2626;
}

QPushButton#TagChip {
    background-color: #1e2233;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 3px 10px;
    color: #94a3b8;
    font-size: 11px;
}

QPushButton#TagChip:hover {
    background-color: #2e3650;
    color: #f472b6;
    border-color: #ec4899;
}

QScrollArea {
    background-color: #0f111a;
    border: none;
}

QProgressBar {
    background-color: #1e2233;
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
    font-size: 11px;
}

QProgressBar::chunk {
    background-color: #ec4899;
    border-radius: 5px;
}

QCheckBox {
    color: #cbd5e1;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #1e2233;
}

QCheckBox::indicator:checked {
    background-color: #ec4899;
    border-color: #f472b6;
}

QFrame#CardFrame {
    background-color: #171926;
    border: 2px solid #252a3d;
    border-radius: 10px;
}

QFrame#CardFrame:hover {
    border-color: #ec4899;
}

QFrame#CardFrameSelected {
    background-color: #1e2035;
    border: 2px solid #ec4899;
    border-radius: 10px;
}
"""

def get_referer_for_url(url: str) -> str:
    if not url:
        return "https://google.com/"
    if "rule34.xxx" in url:
        return "https://rule34.xxx/"
    elif "gelbooru.com" in url:
        return "https://gelbooru.com/"
    elif "danbooru.donmai.us" in url:
        return "https://danbooru.donmai.us/"
    elif "yande.re" in url:
        return "https://yande.re/"
    elif "konachan.com" in url:
        return "https://konachan.com/"
    elif "realbooru.com" in url:
        return "https://realbooru.com/"
    elif "coomer.su" in url:
        return "https://coomer.su/"
    elif "erome.com" in url:
        return "https://www.erome.com/"
    try:
        parsed = urllib.parse.urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/"
    except Exception:
        return "https://google.com/"

class ImageLoaderSignals(QRunnable):
    def __init__(self, post: Dict[str, Any], callback):
        super().__init__()
        self.post = post
        self.callback = callback

    def run(self):
        url = self.post.get("preview_url") or self.post.get("sample_url") or self.post.get("file_url")
        if not url:
            return
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    "Referer": get_referer_for_url(url),
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
                }
            )
            with urllib.request.urlopen(req, timeout=12) as response:
                data = response.read()
                image = QImage.fromData(data)
                if not image.isNull():
                    self.callback(self.post.get("id"), image)
        except Exception:
            pass

class SearchWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, manager: ProviderManager, request: SearchRequest):
        super().__init__()
        self.manager = manager
        self.request = request

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.manager.search(self.request))
            loop.close()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class DownloadWorker(QThread):
    progress = pyqtSignal(dict)
    finished = pyqtSignal(dict)

    def __init__(self, downloader: DownloadManager, posts: List[Dict[str, Any]], settings: Dict[str, Any]):
        super().__init__()
        self.downloader = downloader
        self.posts = posts
        self.settings = settings

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            def on_progress(stats):
                self.progress.emit(stats)

            result = loop.run_until_complete(
                self.downloader.download_posts(
                    posts=self.posts,
                    destination_dir=self.settings.get("download_dir", "./downloads"),
                    naming_pattern=self.settings.get("naming_pattern", "{source}_{id}_{tags}"),
                    create_subfolders=self.settings.get("create_subfolders", True),
                    subfolder_name=self.settings.get("subfolder_name", ""),
                    skip_existing=self.settings.get("skip_existing", True),
                    save_metadata=self.settings.get("save_metadata", True),
                    threads=self.settings.get("threads", 4),
                    progress_callback=on_progress
                )
            )
            loop.close()
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"status": "error", "errors": [str(e)]})

class ImageCardWidget(QFrame):
    def __init__(self, post: Dict[str, Any], on_select_toggle, on_preview):
        super().__init__()
        self.post = post
        self.on_select_toggle = on_select_toggle
        self.on_preview = on_preview
        self.is_selected = False
        self.setObjectName("CardFrame")
        self.setFixedWidth(230)
        self.setFixedHeight(300)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Top Bar: Checkbox & Rating
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self._handle_check)
        top_bar.addWidget(self.checkbox)

        top_bar.addStretch()

        rating = str(post.get("rating", "nsfw")).upper()
        rating_color = "#ef4444" if "EXP" in rating else "#f59e0b" if "QUEST" in rating else "#10b981"
        self.rating_lbl = QLabel(rating[:4])
        self.rating_lbl.setStyleSheet(f"background-color: {rating_color}22; color: {rating_color}; border: 1px solid {rating_color}66; border-radius: 4px; padding: 1px 5px; font-size: 10px; font-weight: bold;")
        top_bar.addWidget(self.rating_lbl)

        layout.addLayout(top_bar)

        # Image Container
        self.img_lbl = QLabel("Загрузка...")
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl.setStyleSheet("background-color: #0f111a; border-radius: 6px; color: #64748b;")
        self.img_lbl.setFixedHeight(180)
        layout.addWidget(self.img_lbl)

        # Bottom Info Bar
        info_bar = QHBoxLayout()
        info_bar.setContentsMargins(0, 0, 0, 0)
        
        w = post.get("width", 0)
        h = post.get("height", 0)
        res_text = f"{w}x{h}" if w and h else post.get("file_ext", "IMG").upper()
        res_lbl = QLabel(res_text)
        res_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        info_bar.addWidget(res_lbl)

        info_bar.addStretch()

        score = post.get("score", 0)
        score_lbl = QLabel(f"★ {score}")
        score_lbl.setStyleSheet("color: #fbbf24; font-size: 11px; font-weight: bold;")
        info_bar.addWidget(score_lbl)

        layout.addLayout(info_bar)

        # Action Buttons
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(0, 0, 0, 0)
        
        self.preview_btn = QPushButton("🔍 Просмотр")
        self.preview_btn.setFixedHeight(26)
        self.preview_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.preview_btn.clicked.connect(lambda: self.on_preview(self.post))
        btn_bar.addWidget(self.preview_btn)

        layout.addLayout(btn_bar)

    def set_image(self, qimage: QImage):
        pixmap = QPixmap.fromImage(qimage)
        scaled = pixmap.scaled(214, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.img_lbl.setPixmap(scaled)

    def _handle_check(self, state):
        self.is_selected = (state == Qt.CheckState.Checked.value or state == 2)
        self.update_style()
        self.on_select_toggle(self.post, self.is_selected)

    def toggle_selected(self, selected: bool):
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(selected)
        self.checkbox.blockSignals(False)
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setObjectName("CardFrameSelected")
        else:
            self.setObjectName("CardFrame")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)

class PreviewDialog(QDialog):
    def __init__(self, post: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.post = post
        self.setWindowTitle(f"Просмотр изображения #{post.get('id')} - {post.get('source')}")
        self.resize(950, 750)
        self.setStyleSheet(DARK_STYLESHEET)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left: Full Image Viewer
        img_scroll = QScrollArea()
        img_scroll.setWidgetResizable(True)
        img_scroll.setStyleSheet("background-color: #0b0d13; border-radius: 8px;")
        
        self.img_lbl = QLabel("Загрузка оригинала...")
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_scroll.setWidget(self.img_lbl)
        layout.addWidget(img_scroll, 3)

        # Right: Info & Controls
        info_panel = QVBoxLayout()
        info_panel.setSpacing(12)

        title = QLabel(f"Post ID: {post.get('id')}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f472b6;")
        info_panel.addWidget(title)

        source_lbl = QLabel(f"Источник: {post.get('source').upper()}")
        info_panel.addWidget(source_lbl)

        res_lbl = QLabel(f"Разрешение: {post.get('width')} x {post.get('height')}")
        info_panel.addWidget(res_lbl)

        rating_lbl = QLabel(f"Рейтинг: {post.get('rating').upper()}")
        info_panel.addWidget(rating_lbl)

        score_lbl = QLabel(f"Оценка / Рейтинг: ★ {post.get('score')}")
        info_panel.addWidget(score_lbl)

        # Tags area
        tags_title = QLabel("Теги:")
        tags_title.setStyleSheet("font-weight: bold; margin-top: 8px;")
        info_panel.addWidget(tags_title)

        tags_scroll = QScrollArea()
        tags_scroll.setWidgetResizable(True)
        tags_scroll.setFixedHeight(220)
        tags_container = QWidget()
        tags_layout = QVBoxLayout(tags_container)
        tags_layout.setContentsMargins(4, 4, 4, 4)
        tags_layout.setSpacing(4)
        
        for t in post.get("tags", []):
            t_lbl = QLabel(f"• {t}")
            t_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
            tags_layout.addWidget(t_lbl)
        tags_layout.addStretch()
        tags_scroll.setWidget(tags_container)
        info_panel.addWidget(tags_scroll)

        info_panel.addStretch()

        download_btn = QPushButton("💾 Сохранить оригинал")
        download_btn.setObjectName("PrimaryBtn")
        download_btn.setFixedHeight(38)
        download_btn.clicked.connect(self._save_single)
        info_panel.addWidget(download_btn)

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(34)
        close_btn.clicked.connect(self.accept)
        info_panel.addWidget(close_btn)

        layout.addLayout(info_panel, 1)

        # Start async full image load
        self._load_full_image()

    def _load_full_image(self):
        url = self.post.get("file_url") or self.post.get("sample_url")
        if not url:
            self.img_lbl.setText("URL не найден")
            return
        
        thread_pool = QThreadPool.globalInstance()
        thread_pool.start(ImageLoaderSignals(self.post, self._on_image_loaded))

    def _on_image_loaded(self, post_id, qimage: QImage):
        pixmap = QPixmap.fromImage(qimage)
        scaled = pixmap.scaled(620, 680, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.img_lbl.setPixmap(scaled)

    def _save_single(self):
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить изображение",
            f"{self.post.get('source')}_{self.post.get('id')}.{self.post.get('file_ext', 'jpg')}",
            "Images (*.png *.jpg *.jpeg *.webp *.gif)"
        )
        if save_path:
            url = self.post.get("file_url") or self.post.get("sample_url")
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                        "Referer": get_referer_for_url(url)
                    }
                )
                with urllib.request.urlopen(req, timeout=30) as response:
                    with open(save_path, "wb") as f:
                        f.write(response.read())
                QMessageBox.information(self, "Успех", "Изображение успешно сохранено!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось скачать: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NSFW Image Hunter & Downloader v1.0")
        self.resize(1280, 850)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(DARK_STYLESHEET)

        self.provider_manager = ProviderManager()
        self.downloader = DownloadManager()
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(8)

        self.current_posts: List[Dict[str, Any]] = []
        self.selected_posts: Dict[str, Dict[str, Any]] = {}
        self.card_widgets: Dict[str, ImageCardWidget] = {}
        self.current_page = 1
        self.settings = load_settings()

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Frame (Logo + Source + Search + Rating)
        header = QFrame()
        header.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(12)

        title = QLabel("🔥 NSFW Image Hunter")
        title.setObjectName("AppTitle")
        header_layout.addWidget(title)

        # Provider Selector
        self.source_combo = QComboBox()
        for p in self.provider_manager.get_providers_list():
            self.source_combo.addItem(p["name"], p["id"])
        self.source_combo.addItem("✨ Все источники (All)", "all")
        header_layout.addWidget(self.source_combo)

        # Rating Filter
        self.rating_combo = QComboBox()
        self.rating_combo.addItem("🔞 Любой рейтинг (All)", "all")
        self.rating_combo.addItem("🔴 Только Explicit (NSFW)", "explicit")
        self.rating_combo.addItem("🟡 Questionable (Ecchi)", "questionable")
        self.rating_combo.addItem("🟢 Safe / General", "safe")
        header_layout.addWidget(self.rating_combo)

        # Search Query Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите имя модели или теги (например: Милена Лисицына, solo bikini)...")
        self.search_input.returnPressed.connect(self.start_search)
        
        # Tag Autocomplete
        completer = QCompleter(POPULAR_TAGS, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.search_input.setCompleter(completer)
        header_layout.addWidget(self.search_input, 2)

        # Search Button
        self.search_btn = QPushButton("🔍 Найти")
        self.search_btn.setObjectName("PrimaryBtn")
        self.search_btn.clicked.connect(self.start_search)
        header_layout.addWidget(self.search_btn)

        main_layout.addWidget(header)

        # 2. Quick Tags & Filters Bar
        sub_bar = QFrame()
        sub_bar.setObjectName("ToolbarFrame")
        sub_layout = QHBoxLayout(sub_bar)
        sub_layout.setContentsMargins(12, 6, 12, 6)
        sub_layout.setSpacing(8)

        quick_label = QLabel("Популярные теги:")
        quick_label.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold;")
        sub_layout.addWidget(quick_label)

        sample_tags = ["solo", "1girl", "highres", "waifu", "bikini", "lingerie", "ass", "breasts", "wallpaper", "cyberpunk"]
        for tag in sample_tags:
            btn = QPushButton(f"+{tag}")
            btn.setObjectName("TagChip")
            btn.clicked.connect(lambda _, t=tag: self._add_tag_to_search(t))
            sub_layout.addWidget(btn)

        sub_layout.addStretch()

        # Orientation filter
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItem("📐 Любая ориентация", "all")
        self.aspect_combo.addItem("🖼️ Горизонтальная (Обои)", "landscape")
        self.aspect_combo.addItem("📱 Вертикальная (Портрет)", "portrait")
        self.aspect_combo.addItem("⏹️ Квадратная", "square")
        self.aspect_combo.currentIndexChanged.connect(self.start_search)
        sub_layout.addWidget(self.aspect_combo)

        # Min resolution filter
        self.res_combo = QComboBox()
        self.res_combo.addItem("⚡ Любое разрешение", 0)
        self.res_combo.addItem("💎 >= 1080p (FHD)", 1080)
        self.res_combo.addItem("🌟 >= 1440p (2K)", 1440)
        self.res_combo.addItem("👑 >= 2160p (4K)", 2160)
        self.res_combo.currentIndexChanged.connect(self.start_search)
        sub_layout.addWidget(self.res_combo)

        main_layout.addWidget(sub_bar)

        # 3. Action Toolbar (Selection Controls & Download Trigger)
        toolbar = QFrame()
        toolbar.setObjectName("ToolbarFrame")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(12, 6, 12, 6)
        tb_layout.setSpacing(10)

        self.btn_select_all = QPushButton("☑️ Выбрать все")
        self.btn_select_all.clicked.connect(self.select_all)
        tb_layout.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("⬜ Снять выбор")
        self.btn_deselect_all.clicked.connect(self.deselect_all)
        tb_layout.addWidget(self.btn_deselect_all)

        self.btn_invert_select = QPushButton("🔄 Инвертировать")
        self.btn_invert_select.clicked.connect(self.invert_selection)
        tb_layout.addWidget(self.btn_invert_select)

        self.btn_select_highres = QPushButton("✨ Только High-Res (>=1080p)")
        self.btn_select_highres.clicked.connect(self.select_highres)
        tb_layout.addWidget(self.btn_select_highres)

        self.selected_count_lbl = QLabel("Выбрано: 0 картинок")
        self.selected_count_lbl.setStyleSheet("color: #ec4899; font-weight: bold; font-size: 13px; margin-left: 10px;")
        tb_layout.addWidget(self.selected_count_lbl)

        tb_layout.addStretch()

        # Destination folder
        folder_lbl = QLabel("Папка:")
        folder_lbl.setStyleSheet("color: #94a3b8;")
        tb_layout.addWidget(folder_lbl)

        self.folder_input = QLineEdit(self.settings.get("download_dir", "./downloads"))
        self.folder_input.setFixedWidth(200)
        tb_layout.addWidget(self.folder_input)

        self.folder_btn = QPushButton("📁 Обзор...")
        self.folder_btn.clicked.connect(self._choose_folder)
        tb_layout.addWidget(self.folder_btn)

        # Download Selected Button
        self.download_btn = QPushButton("⚡ Скачать выбранные (0)")
        self.download_btn.setObjectName("SuccessBtn")
        self.download_btn.setFixedHeight(34)
        self.download_btn.clicked.connect(self.start_download)
        tb_layout.addWidget(self.download_btn)

        main_layout.addWidget(toolbar)

        # 4. Main Gallery Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.gallery_widget = QWidget()
        self.gallery_grid = QGridLayout(self.gallery_widget)
        self.gallery_grid.setContentsMargins(16, 16, 16, 16)
        self.gallery_grid.setSpacing(14)
        self.gallery_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll_area.setWidget(self.gallery_widget)
        main_layout.addWidget(self.scroll_area, 1)

        # 5. Footer & Pagination & Progress Frame
        footer = QFrame()
        footer.setObjectName("FooterFrame")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(12, 8, 12, 8)
        footer_layout.setSpacing(8)

        # Pagination row
        page_row = QHBoxLayout()
        self.prev_page_btn = QPushButton("◀ Предыдущая")
        self.prev_page_btn.clicked.connect(self._prev_page)
        page_row.addWidget(self.prev_page_btn)

        self.page_lbl = QLabel("Страница 1")
        self.page_lbl.setStyleSheet("font-weight: bold; color: #f8fafc;")
        page_row.addWidget(self.page_lbl)

        self.next_page_btn = QPushButton("Следующая ▶")
        self.next_page_btn.clicked.connect(self._next_page)
        page_row.addWidget(self.next_page_btn)

        page_row.addStretch()

        self.status_lbl = QLabel("Готов к поиску. Введите теги и нажмите 'Найти'.")
        self.status_lbl.setStyleSheet("color: #94a3b8;")
        page_row.addWidget(self.status_lbl)

        footer_layout.addLayout(page_row)

        # Progress bar row (hidden by default)
        self.progress_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setValue(0)
        self.progress_row.addWidget(self.progress_bar, 3)

        self.progress_status_lbl = QLabel("")
        self.progress_status_lbl.setStyleSheet("color: #38bdf8; font-size: 11px;")
        self.progress_row.addWidget(self.progress_status_lbl, 1)

        self.cancel_dl_btn = QPushButton("Отмена")
        self.cancel_dl_btn.setObjectName("DangerBtn")
        self.cancel_dl_btn.setFixedHeight(24)
        self.cancel_dl_btn.clicked.connect(self._cancel_download)
        self.progress_row.addWidget(self.cancel_dl_btn)

        footer_layout.addLayout(self.progress_row)

        main_layout.addWidget(footer)

    def _add_tag_to_search(self, tag: str):
        curr = self.search_input.text().strip()
        if tag not in curr.split():
            self.search_input.setText(f"{curr} {tag}".strip())
        self.start_search()

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения картинок", self.folder_input.text())
        if folder:
            self.folder_input.setText(folder)
            self.settings["download_dir"] = folder
            save_settings(self.settings)

    def start_search(self):
        query = self.search_input.text().strip()
        source = self.source_combo.currentData()
        rating = self.rating_combo.currentData()
        aspect = self.aspect_combo.currentData()
        min_res = self.res_combo.currentData()

        self.search_btn.setEnabled(False)
        self.status_lbl.setText("Поиск изображений... Пожалуйста, подождите.")

        # Clear existing cards
        self._clear_gallery()

        req = SearchRequest(
            query=query,
            source=source,
            page=self.current_page,
            limit=40,
            rating=rating,
            aspect_ratio=aspect,
            min_width=min_res,
            min_height=min_res
        )

        self.search_worker = SearchWorker(self.provider_manager, req)
        self.search_worker.finished.connect(self._on_search_finished)
        self.search_worker.error.connect(self._on_search_error)
        self.search_worker.start()

    def _on_search_finished(self, result: dict):
        self.search_btn.setEnabled(True)
        self.current_posts = result.get("posts", [])
        total = len(self.current_posts)
        self.page_lbl.setText(f"Страница {self.current_page}")

        errors = result.get("errors", [])
        if errors:
            self.status_lbl.setText(f"Найдено: {total} картинок. ({errors[0]})")
        else:
            self.status_lbl.setText(f"Найдено: {total} картинок по запросу '{result.get('query')}'.")

        self._render_cards()

    def _on_search_error(self, err: str):
        self.search_btn.setEnabled(True)
        self.status_lbl.setText(f"Ошибка поиска: {err}")
        QMessageBox.warning(self, "Ошибка поиска", f"Не удалось выполнить поиск: {err}")

    def _clear_gallery(self):
        for i in reversed(range(self.gallery_grid.count())):
            item = self.gallery_grid.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
        self.card_widgets.clear()

    def _render_cards(self):
        self._clear_gallery()
        columns = 5  # Responsive columns
        
        for idx, post in enumerate(self.current_posts):
            card = ImageCardWidget(post, self._on_card_select, self._open_preview)
            post_id = str(post.get("id"))
            self.card_widgets[post_id] = card
            
            # Check if was previously selected
            if post_id in self.selected_posts:
                card.toggle_selected(True)

            row = idx // columns
            col = idx % columns
            self.gallery_grid.addWidget(card, row, col)

            # Request thumbnail async
            self.thread_pool.start(ImageLoaderSignals(post, self._on_thumbnail_loaded))

        self._update_selection_counter()

    def _on_thumbnail_loaded(self, post_id: str, qimage: QImage):
        if post_id in self.card_widgets:
            self.card_widgets[post_id].set_image(qimage)

    def _on_card_select(self, post: Dict[str, Any], is_selected: bool):
        post_id = str(post.get("id"))
        if is_selected:
            self.selected_posts[post_id] = post
        else:
            self.selected_posts.pop(post_id, None)
        self._update_selection_counter()

    def _update_selection_counter(self):
        count = len(self.selected_posts)
        self.selected_count_lbl.setText(f"Выбрано: {count} картинок")
        self.download_btn.setText(f"⚡ Скачать выбранные ({count})")
        self.download_btn.setEnabled(count > 0)

    def select_all(self):
        for post in self.current_posts:
            pid = str(post.get("id"))
            self.selected_posts[pid] = post
            if pid in self.card_widgets:
                self.card_widgets[pid].toggle_selected(True)
        self._update_selection_counter()

    def deselect_all(self):
        self.selected_posts.clear()
        for card in self.card_widgets.values():
            card.toggle_selected(False)
        self._update_selection_counter()

    def invert_selection(self):
        for post in self.current_posts:
            pid = str(post.get("id"))
            if pid in self.selected_posts:
                self.selected_posts.pop(pid, None)
                if pid in self.card_widgets:
                    self.card_widgets[pid].toggle_selected(False)
            else:
                self.selected_posts[pid] = post
                if pid in self.card_widgets:
                    self.card_widgets[pid].toggle_selected(True)
        self._update_selection_counter()

    def select_highres(self):
        for post in self.current_posts:
            pid = str(post.get("id"))
            w = post.get("width", 0)
            h = post.get("height", 0)
            if w >= 1920 or h >= 1080:
                self.selected_posts[pid] = post
                if pid in self.card_widgets:
                    self.card_widgets[pid].toggle_selected(True)
            else:
                self.selected_posts.pop(pid, None)
                if pid in self.card_widgets:
                    self.card_widgets[pid].toggle_selected(False)
        self._update_selection_counter()

    def _open_preview(self, post: Dict[str, Any]):
        dialog = PreviewDialog(post, self)
        dialog.exec()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.start_search()

    def _next_page(self):
        self.current_page += 1
        self.start_search()

    def start_download(self):
        if not self.selected_posts:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите хотя бы одно изображение для скачивания.")
            return

        dest_dir = self.folder_input.text().strip() or "./downloads"
        settings = dict(self.settings)
        settings["download_dir"] = dest_dir
        settings["subfolder_name"] = self.search_input.text().strip() or "general"

        posts_to_dl = list(self.selected_posts.values())
        
        self.progress_bar.setValue(0)
        self.progress_status_lbl.setText("Подготовка к скачиванию...")
        self.download_btn.setEnabled(False)

        self.dl_worker = DownloadWorker(self.downloader, posts_to_dl, settings)
        self.dl_worker.progress.connect(self._on_dl_progress)
        self.dl_worker.finished.connect(self._on_dl_finished)
        self.dl_worker.start()

    def _on_dl_progress(self, stats: dict):
        total = stats.get("total", 1)
        completed = stats.get("completed", 0)
        percent = int(stats.get("progress_percent", 0))
        speed = stats.get("speed_kbps", 0)
        cur_file = stats.get("current_file", "")
        
        self.progress_bar.setValue(percent)
        self.progress_status_lbl.setText(f"Скачано: {completed}/{total} ({speed} KB/s) | {cur_file}")

    def _on_dl_finished(self, stats: dict):
        self.download_btn.setEnabled(True)
        completed = stats.get("completed", 0)
        failed = stats.get("failed", 0)
        skipped = stats.get("skipped", 0)
        dest = self.folder_input.text()

        msg = f"Загрузка завершена!\n\nУспешно скачано: {completed}\nПропущено дубликатов: {skipped}\nОшибок: {failed}\n\nПапка: {dest}"
        QMessageBox.information(self, "Загрузка завершена", msg)
        self.progress_status_lbl.setText(f"Завершено. Скачано: {completed} файлов.")

    def _cancel_download(self):
        self.downloader.cancel()
        self.progress_status_lbl.setText("Отмена загрузки...")

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
