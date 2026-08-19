import sys
import os
import io
import asyncio
import json
import webbrowser
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, QLabel, QScrollArea, QGridLayout,
    QCheckBox, QFileDialog, QProgressBar, QDialog, QMessageBox, QFrame,
    QSizePolicy, QCompleter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRunnable, QThreadPool
from PyQt6.QtGui import QPixmap, QImage, QCursor

from core.models import Post, SearchRequest
from core.providers.manager import ProviderManager
from core.downloader import DownloadManager
from core.tag_suggest import POPULAR_TAGS
from core.settings import load_settings, save_settings
from core.scraper_engine import extract_images_from_url

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

QFrame#GrabberFrame {
    background-color: #1a1528;
    border-bottom: 1px solid #ec4899;
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

QLineEdit {
    background-color: #1e2233;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 12px;
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
    min-width: 140px;
}

QComboBox QAbstractItemView {
    background-color: #1e2233;
    color: #f8fafc;
    selection-background-color: #ec4899;
    border: 1px solid #334155;
}

QPushButton {
    background-color: #282e44;
    border: 1px solid #3b4461;
    border-radius: 8px;
    padding: 6px 14px;
    color: #f1f5f9;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #373f5c;
    border-color: #ec4899;
}

QPushButton#PrimaryBtn {
    background-color: #ec4899;
    border: 1px solid #f472b6;
    color: #ffffff;
    font-weight: bold;
}

QPushButton#PrimaryBtn:hover {
    background-color: #db2777;
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

QPushButton#GrabBtn {
    background-color: #8b5cf6;
    border: 1px solid #a78bfa;
    color: #ffffff;
    font-weight: bold;
}

QPushButton#GrabBtn:hover {
    background-color: #7c3aed;
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
}

QProgressBar::chunk {
    background-color: #ec4899;
    border-radius: 5px;
}

QCheckBox {
    color: #cbd5e1;
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

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

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
        
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                        "Referer": get_referer_for_url(url),
                        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
                    }
                )
                with urllib.request.urlopen(req, context=ssl_context, timeout=15) as response:
                    data = response.read()
                    image = QImage.fromData(data)
                    if not image.isNull():
                        self.callback(self.post.get("id"), image)
                        break
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

class UrlGrabWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            posts = loop.run_until_complete(extract_images_from_url(self.url))
            loop.close()
            self.finished.emit([p.to_dict() for p in posts])
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

        # Top Bar: Checkbox & Source
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self._handle_check)
        top_bar.addWidget(self.checkbox)

        top_bar.addStretch()

        source_name = str(post.get("source", "WEB"))
        self.rating_lbl = QLabel(source_name[:12])
        self.rating_lbl.setStyleSheet("background-color: #ec489922; color: #ec4899; border: 1px solid #ec489966; border-radius: 4px; padding: 1px 5px; font-size: 10px; font-weight: bold;")
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

        score = post.get("score", 950)
        score_lbl = QLabel(f"★ {score}")
        score_lbl.setStyleSheet("color: #fbbf24; font-size: 11px; font-weight: bold;")
        info_bar.addWidget(score_lbl)

        layout.addLayout(info_bar)

        # Action Buttons
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(0, 0, 0, 0)
        
        self.preview_btn = QPushButton("🔍 Просмотр оригинала")
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
        self.setWindowTitle(f"Просмотр изображения - {post.get('source')}")
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

        title = QLabel(f"Источник: {post.get('source')}")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #f472b6;")
        info_panel.addWidget(title)

        res_lbl = QLabel(f"Разрешение: {post.get('width')} x {post.get('height')}")
        info_panel.addWidget(res_lbl)

        # Tags area
        tags_title = QLabel("Теги:")
        tags_title.setStyleSheet("font-weight: bold; margin-top: 8px;")
        info_panel.addWidget(tags_title)

        tags_scroll = QScrollArea()
        tags_scroll.setWidgetResizable(True)
        tags_scroll.setFixedHeight(200)
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

        download_btn = QPushButton("💾 Сохранить этот оригинал")
        download_btn.setObjectName("PrimaryBtn")
        download_btn.setFixedHeight(38)
        download_btn.clicked.connect(self._save_single)
        info_panel.addWidget(download_btn)

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(34)
        close_btn.clicked.connect(self.accept)
        info_panel.addWidget(close_btn)

        layout.addLayout(info_panel, 1)

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
            f"photo_{self.post.get('id')}.{self.post.get('file_ext', 'jpg')}",
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
                with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
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
        self.thread_pool.setMaxThreadCount(10)

        self.current_posts: List[Dict[str, Any]] = []
        self.selected_posts: Dict[str, Dict[str, Any]] = {}
        self.card_widgets: Dict[str, ImageCardWidget] = {}
        self.current_page = 1
        self.is_loading = False
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
        self.search_input.setText("Милена Лисицына")
        self.search_input.setPlaceholderText("Введите имя модели или теги (например: Милена Лисицына, solo bikini)...")
        self.search_input.returnPressed.connect(lambda: self.start_search(reset=True))
        header_layout.addWidget(self.search_input, 2)

        # Search Button
        self.search_btn = QPushButton("🔍 Найти")
        self.search_btn.setObjectName("PrimaryBtn")
        self.search_btn.clicked.connect(lambda: self.start_search(reset=True))
        header_layout.addWidget(self.search_btn)

        main_layout.addWidget(header)

        # 2. URL Grabber Frame
        grab_frame = QFrame()
        grab_frame.setObjectName("GrabberFrame")
        gf_layout = QHBoxLayout(grab_frame)
        gf_layout.setContentsMargins(12, 6, 12, 6)
        gf_layout.setSpacing(8)

        grab_lbl = QLabel("🌐 Захват по ссылке:")
        grab_lbl.setStyleSheet("color: #a78bfa; font-weight: bold; font-size: 12px;")
        gf_layout.addWidget(grab_lbl)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Вставьте ссылку на страницу Яндекс/Bing/EroMe/Coomer/Альбом...")
        self.url_input.returnPressed.connect(self.start_url_grab)
        gf_layout.addWidget(self.url_input, 2)

        self.grab_btn = QPushButton("⚡ Захватить все фото со страницы")
        self.grab_btn.setObjectName("GrabBtn")
        self.grab_btn.clicked.connect(self.start_url_grab)
        gf_layout.addWidget(self.grab_btn)

        # Quick Browser Buttons
        btn_yandex = QPushButton("🇷🇺 Открыть Яндекс")
        btn_yandex.clicked.connect(lambda: self._open_browser_search("yandex"))
        gf_layout.addWidget(btn_yandex)

        btn_bing = QPushButton("🌐 Открыть Bing 18+")
        btn_bing.clicked.connect(lambda: self._open_browser_search("bing"))
        gf_layout.addWidget(btn_bing)

        btn_erome = QPushButton("🔥 Открыть EroMe")
        btn_erome.clicked.connect(lambda: self._open_browser_search("erome"))
        gf_layout.addWidget(btn_erome)

        main_layout.addWidget(grab_frame)

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

        # 4. Main Gallery Scroll Area with Infinite Scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)
        
        self.gallery_widget = QWidget()
        self.gallery_grid = QGridLayout(self.gallery_widget)
        self.gallery_grid.setContentsMargins(16, 16, 16, 16)
        self.gallery_grid.setSpacing(14)
        self.gallery_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll_area.setWidget(self.gallery_widget)
        main_layout.addWidget(self.scroll_area, 1)

        # 5. Footer Frame (Status & Progress)
        footer = QFrame()
        footer.setObjectName("FooterFrame")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(12, 8, 12, 8)
        footer_layout.setSpacing(8)

        status_row = QHBoxLayout()
        self.status_lbl = QLabel("Готов к работе. Введите запрос или скрольте вниз для бесконечной подгрузки.")
        self.status_lbl.setStyleSheet("color: #94a3b8;")
        status_row.addWidget(self.status_lbl, 1)

        self.load_more_btn = QPushButton("⚡ Загрузить ещё фото")
        self.load_more_btn.clicked.connect(self.load_more)
        status_row.addWidget(self.load_more_btn)

        footer_layout.addLayout(status_row)

        # Progress bar row
        self.progress_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setValue(0)
        self.progress_row.addWidget(self.progress_bar, 3)

        self.progress_status_lbl = QLabel("")
        self.progress_status_lbl.setStyleSheet("color: #38bdf8; font-size: 11px;")
        self.progress_row.addWidget(self.progress_status_lbl, 1)

        self.cancel_dl_btn = QPushButton("Отмена")
        self.cancel_dl_btn.setFixedHeight(24)
        self.cancel_dl_btn.clicked.connect(self._cancel_download)
        self.progress_row.addWidget(self.cancel_dl_btn)

        footer_layout.addLayout(self.progress_row)

        main_layout.addWidget(footer)

    def _on_scroll_changed(self, value):
        max_val = self.scroll_area.verticalScrollBar().maximum()
        if max_val > 0 and value >= max_val - 200 and not self.is_loading:
            self.load_more()

    def _open_browser_search(self, engine: str):
        q = urllib.parse.quote_plus(self.search_input.text().strip() or "Милена Лисицына")
        target_url = ""
        if engine == "yandex":
            target_url = f"https://yandex.ru/images/search?text={q}"
        elif engine == "bing":
            target_url = f"https://www.bing.com/images/search?q={q}&adlt=off"
        elif engine == "erome":
            target_url = f"https://www.erome.com/search?q={q}"

        self.url_input.setText(target_url)
        webbrowser.open(target_url)
        self.status_lbl.setText("Страница открыта в браузере. Скопируйте ссылку и нажмите 'Захватить'.")

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения картинок", self.folder_input.text())
        if folder:
            self.folder_input.setText(folder)
            self.settings["download_dir"] = folder
            save_settings(self.settings)

    def start_url_grab(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, вставьте ссылку в поле захвата!")
            return

        self.grab_btn.setEnabled(False)
        self.status_lbl.setText("Захват всех полноразмерных картинок со страницы...")
        self._clear_gallery()

        self.grab_worker = UrlGrabWorker(url)
        self.grab_worker.finished.connect(self._on_grab_finished)
        self.grab_worker.error.connect(self._on_grab_error)
        self.grab_worker.start()

    def _on_grab_finished(self, posts: list):
        self.grab_btn.setEnabled(True)
        self.current_posts = posts
        total = len(posts)
        if total == 0:
            self.status_lbl.setText("На указанной странице не найдено прямых картинок.")
            QMessageBox.information(self, "Захват", "На странице не найдено прямых картинок. Попробуйте скопировать ссылку на конкретный альбом или результаты поиска.")
        else:
            self.status_lbl.setText(f"Успешно захвачено {total} полноразмерных фото со страницы!")
            self._render_cards()

    def _on_grab_error(self, err: str):
        self.grab_btn.setEnabled(True)
        self.status_lbl.setText(f"Ошибка захвата: {err}")
        QMessageBox.warning(self, "Ошибка захвата", f"Не удалось захватить фото: {err}")

    def start_search(self, reset: bool = True):
        if self.is_loading:
            return

        if reset:
            self.current_page = 1
            self._clear_gallery()
            self.current_posts = []

        query = self.search_input.text().strip()
        source = self.source_combo.currentData()
        rating = self.rating_combo.currentData()

        self.is_loading = True
        self.search_btn.setEnabled(False)
        self.load_more_btn.setEnabled(False)
        self.status_lbl.setText(f"Загрузка фото (порция {self.current_page})... Скрольте вниз для продолжения.")

        req = SearchRequest(
            query=query,
            source=source,
            page=self.current_page,
            limit=40,
            rating=rating
        )

        self.search_worker = SearchWorker(self.provider_manager, req)
        self.search_worker.finished.connect(self._on_search_finished)
        self.search_worker.error.connect(self._on_search_error)
        self.search_worker.start()

    def load_more(self):
        if not self.is_loading and self.current_posts:
            self.current_page += 1
            self.start_search(reset=False)

    def _on_search_finished(self, result: dict):
        self.is_loading = False
        self.search_btn.setEnabled(True)
        self.load_more_btn.setEnabled(True)

        new_posts = result.get("posts", [])
        
        # Deduplicate and append
        seen_ids = {str(p.get("id")) for p in self.current_posts}
        added_count = 0
        for p in new_posts:
            pid = str(p.get("id"))
            if pid not in seen_ids:
                seen_ids.add(pid)
                self.current_posts.append(p)
                added_count += 1

        total = len(self.current_posts)
        errors = result.get("errors", [])

        if total == 0:
            self.status_lbl.setText(errors[0] if errors else "Ничего не найдено.")
        else:
            self.status_lbl.setText(f"Всего загружено: {total} картинок. Скрольте вниз для автоматической подгрузки!")

        self._render_cards()

    def _on_search_error(self, err: str):
        self.is_loading = False
        self.search_btn.setEnabled(True)
        self.load_more_btn.setEnabled(True)
        self.status_lbl.setText(f"Ошибка: {err}")

    def _clear_gallery(self):
        for i in reversed(range(self.gallery_grid.count())):
            item = self.gallery_grid.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
        self.card_widgets.clear()

    def _render_cards(self):
        columns = 5
        existing_count = len(self.card_widgets)
        
        for idx in range(existing_count, len(self.current_posts)):
            post = self.current_posts[idx]
            card = ImageCardWidget(post, self._on_card_select, self._open_preview)
            post_id = str(post.get("id"))
            self.card_widgets[post_id] = card
            
            if post_id in self.selected_posts:
                card.toggle_selected(True)

            row = idx // columns
            col = idx % columns
            self.gallery_grid.addWidget(card, row, col)

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

    def start_download(self):
        if not self.selected_posts:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите хотя бы одно изображение для скачивания.")
            return

        dest_dir = self.folder_input.text().strip() or "./downloads"
        settings = dict(self.settings)
        settings["download_dir"] = dest_dir
        settings["subfolder_name"] = self.search_input.text().strip() or "models"

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

        msg = f"Загрузка завершена!\n\nУспешно скачано: {completed}\nПропущено: {skipped}\nОшибок: {failed}\n\nПапка: {dest}"
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
