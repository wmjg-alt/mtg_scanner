from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QFrame, QScrollArea, QStackedWidget, QPushButton, QGridLayout, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import os
import requests
from data.db_manager import DBManager
import config

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MTG Collection Dashboard")
        self.resize(1300, 900)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: white; }
            QPushButton { background-color: #333; color: white; border: 1px solid #555; padding: 5px; border-radius: 4px; }
            QPushButton:hover { background-color: #444; border-color: #888; }
            QScrollArea { border: none; background-color: #1e1e1e; }
            QWidget { background-color: #1e1e1e; color: white; }
        """)
        
        self.db = DBManager()
        
        # Ensure cache directory exists
        self.cache_dir = os.path.join(config.BASE_DIR, "data", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        
        # Pages
        self.home_page = None # Lazy load
        self.refresh_home()

    def get_cached_image(self, url, card_id):
        """Downloads image if not cached, returns local path"""
        if not url: return None
        
        # Create a safe filename from the URL or ID
        ext = url.split('.')[-1].split('?')[0]
        filename = f"{card_id}.{ext}"
        local_path = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(local_path):
            return local_path
            
        # Download
        try:
            print(f"Downloading cache: {url}")
            response = requests.get(url, headers={"User-Agent": config.API_USER_AGENT})
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return local_path
        except Exception as e:
            print(f"Failed to download image: {e}")
            
        return None

    def refresh_home(self):
        # Re-create home page to update stats
        if self.home_page:
            self.central_stack.removeWidget(self.home_page)
            self.home_page.deleteLater()
            
        self.stats = self.db.get_dashboard_stats()
        self.home_page = self.create_home_page()
        self.central_stack.insertWidget(0, self.home_page)
        self.central_stack.setCurrentIndex(0)

    # --- HOME PAGE ---
    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Header
        header = self.create_stats_header(self.stats)
        layout.addWidget(header)
        
        # Chart
        if self.stats['colors']:
            chart = self.create_chart(self.stats['colors'])
            layout.addWidget(chart, stretch=1)
        
        # Recent Scans
        gallery = self.create_recent_gallery()
        layout.addWidget(gallery)
        
        return page

    def create_stats_header(self, stats):
        frame = QFrame()
        frame.setStyleSheet("background-color: #2d2d2d; border-radius: 8px;")
        layout = QHBoxLayout(frame)
        
        def add_box(title, val, color="#fff"):
            v = QVBoxLayout()
            l1 = QLabel(title)
            l1.setStyleSheet("color: #aaa; font-size: 14px; background: transparent;")
            l2 = QLabel(str(val))
            l2.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold; background: transparent;")
            v.addWidget(l1)
            v.addWidget(l2)
            layout.addLayout(v)

        add_box("Total Cards", stats['total_count'])
        add_box("Total Value", f"${stats['total_value']}", "#4CAF50")
        
        if stats['top_card']:
            tc = stats['top_card']
            btn = QPushButton(f"🏆 Top: {tc['display_name']} (${tc['price_usd']})")
            btn.setStyleSheet("color: #FFD700; background: transparent; border: none; font-size: 18px; font-weight: bold;")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda: self.show_details(tc['tracker_id']))
            layout.addWidget(btn)
            
        return frame

    def create_chart(self, colors_data):
        frame = QFrame()
        layout = QHBoxLayout(frame)
        
        canvas = FigureCanvas(Figure(figsize=(5, 4), facecolor='#1e1e1e'))
        ax = canvas.figure.add_subplot(111)
        
        labels = list(colors_data.keys())
        values = list(colors_data.values())
        
        cmap = {"W": "#F0E6BC", "U": "#4169E1", "B": "#A9A9A9", "R": "#F08080", "G": "#228B22", "Multi": "#FFD700", "Colorless": "#C0C0C0"}
        chart_colors = [cmap.get(l, "#fff") for l in labels]
        
        wedges, _, _ = ax.pie(values, labels=labels, autopct='%1.1f%%', colors=chart_colors)
        ax.set_title("Collection by Color (Click to Filter)", color='white')
        
        def on_pick(event):
            if event.artist in wedges:
                idx = wedges.index(event.artist)
                self.show_list(labels[idx])

        for w in wedges: w.set_picker(True)
        canvas.figure.canvas.mpl_connect('pick_event', on_pick)
        
        layout.addWidget(canvas)
        return frame

    def create_recent_gallery(self):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.addWidget(QLabel("Recent Scans"))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        h_layout = QHBoxLayout(content)
        h_layout.setAlignment(Qt.AlignLeft)
        
        scans = self.db.get_recent_scans(8)
        
        for card in scans:
            btn = QPushButton()
            btn.setFixedSize(120, 180)
            btn.setStyleSheet("border: none;")
            btn.setCursor(Qt.PointingHandCursor)
            v = QVBoxLayout(btn)
            v.setContentsMargins(0,0,0,0)
            
            img = QLabel()
            if card['local_image_path'] and os.path.exists(card['local_image_path']):
                pix = QPixmap(card['local_image_path']).scaled(120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img.setPixmap(pix)
            img.setAlignment(Qt.AlignCenter)
            img.setStyleSheet("background: transparent;")
            
            lbl = QLabel(f"${card['price_usd']}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 10px; color: #4CAF50; background: transparent;")
            
            v.addWidget(img)
            v.addWidget(lbl)
            
            btn.clicked.connect(lambda checked=False, tid=card['tracker_id']: self.show_details(tid))
            h_layout.addWidget(btn)
            
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return frame

    # --- LIST PAGE ---
    def show_list(self, color_filter):
        cards = self.db.get_cards_by_filter(color=color_filter, limit=100)
        
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Nav
        top_bar = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.refresh_home)
        top_bar.addWidget(back_btn)
        
        title = QLabel(f"Filter: {color_filter}")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_bar.addWidget(title)
        layout.addLayout(top_bar)
        
        # Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        
        row, col = 0, 0
        for card in cards:
            # Card Button Container
            wrapper = QFrame()
            wrapper.setFixedSize(160, 240)
            wrapper.setStyleSheet("background-color: #2d2d2d; border-radius: 8px;")
            
            vbox = QVBoxLayout(wrapper)
            vbox.setContentsMargins(5,5,5,5)
            
            # Use WEB Image for the list view if available, else local
            # We fetch 'image_url' via db query. 
            # Note: You might need to update get_cards_by_filter to select image_url
            
            # Let's assume we update the query in DBManager or just use local scan for list speed
            # Using Local Scan for list is faster and confirms what you actually have
            img_path = card['local_image_path']
            
            img_lbl = QLabel()
            img_lbl.setAlignment(Qt.AlignCenter)
            if img_path and os.path.exists(img_path):
                pix = QPixmap(img_path).scaled(140, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_lbl.setPixmap(pix)
            else:
                img_lbl.setText(card['display_name'])
                
            price_lbl = QLabel(f"${card['price_usd']}")
            price_lbl.setAlignment(Qt.AlignCenter)
            price_lbl.setStyleSheet("color: #4CAF50;")
            
            vbox.addWidget(img_lbl)
            vbox.addWidget(price_lbl)
            
            # Invisible button overlay for click
            btn = QPushButton(wrapper)
            btn.setGeometry(0, 0, 160, 240)
            btn.setStyleSheet("background: transparent; border: none;")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, tid=card['tracker_id']: self.show_details(tid))
            
            grid.addWidget(wrapper, row, col)
            col += 1
            if col > 4:
                col = 0
                row += 1
                
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        self.central_stack.addWidget(page)
        self.central_stack.setCurrentWidget(page)

    # --- DETAIL PAGE ---
    def show_details(self, tracker_id):
        card = self.db.get_card_details(tracker_id)
        if not card: return
        
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Header
        top = QHBoxLayout()
        back = QPushButton("← Back")
        back.setFixedWidth(100)
        back.clicked.connect(self.refresh_home)
        top.addWidget(back)
        
        del_btn = QPushButton("🗑️ Remove Card")
        del_btn.setFixedWidth(120)
        del_btn.setStyleSheet("background-color: #8b0000; border: 1px solid #ff4444;")
        del_btn.clicked.connect(lambda: self.delete_card(tracker_id, card['display_name']))
        top.addStretch()
        top.addWidget(del_btn)
        
        layout.addLayout(top)
        
        # Main Content
        content = QHBoxLayout()
        
        # LEFT: Local Scan
        scan_box = QVBoxLayout()
        lbl_scan = QLabel("Your Scan")
        lbl_scan.setAlignment(Qt.AlignCenter)
        scan_box.addWidget(lbl_scan)
        
        scan_img = QLabel()
        if card['local_image_path'] and os.path.exists(card['local_image_path']):
            pix = QPixmap(card['local_image_path']).scaled(350, 490, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            scan_img.setPixmap(pix)
        scan_box.addWidget(scan_img)
        content.addLayout(scan_box)
        
        # RIGHT: Web Image
        web_box = QVBoxLayout()
        lbl_web = QLabel("Official Scryfall Image")
        lbl_web.setAlignment(Qt.AlignCenter)
        web_box.addWidget(lbl_web)
        
        web_img = QLabel("Downloading...")
        web_img.setAlignment(Qt.AlignCenter)
        web_box.addWidget(web_img)
        content.addLayout(web_box)
        
        # Load Web Image (Cached)
        web_path = self.get_cached_image(card['image_url'], card['scryfall_id'])
        if web_path:
            pix = QPixmap(web_path).scaled(350, 490, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            web_img.setPixmap(pix)
            web_img.setText("")
        else:
            web_img.setText("No Image Available")

        # INFO TEXT
        info_col = QVBoxLayout()
        info_col.setAlignment(Qt.AlignTop)
        
        name = QLabel(card['display_name'])
        name.setStyleSheet("font-size: 32px; font-weight: bold; margin-bottom: 10px;")
        info_col.addWidget(name)
        
        meta = QLabel(f"Set: {card['set_name']} ({card['set_code'].upper()})\nType: {card['type_line']}")
        meta.setStyleSheet("font-size: 16px; color: #ccc;")
        info_col.addWidget(meta)
        
        price = QLabel(f"\nPrice: ${card['price_usd']}")
        price.setStyleSheet("font-size: 24px; color: #4CAF50; font-weight: bold;")
        info_col.addWidget(price)
        
        oracle = QLabel(f"\n{card['oracle_text']}")
        oracle.setWordWrap(True)
        oracle.setStyleSheet("background-color: #333; padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.4;")
        info_col.addWidget(oracle)
        
        content.addLayout(info_col)
        layout.addLayout(content)
        
        self.central_stack.addWidget(page)
        self.central_stack.setCurrentWidget(page)

    def delete_card(self, tracker_id, name):
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                     f"Are you sure you want to delete '{name}' from your collection?\nThis cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.db.delete_scan(tracker_id)
            self.refresh_home()