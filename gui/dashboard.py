from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QFrame, QScrollArea, QStackedWidget, QPushButton, QGridLayout, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import os
import requests
from data.db_manager import DBManager
from gui.ui_util import get_app_icon
import config

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MTG Collection Dashboard")
        self.setWindowIcon(get_app_icon()) # NEW
        self.resize(config.DEFAULT_WINDOW_WIDTH, config.DEFAULT_WINDOW_HEIGHT)
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; color: white; }
            QPushButton { background-color: #333; color: white; border: 1px solid #555; padding: 5px; border-radius: 4px; }
            QPushButton:hover { background-color: #444; border-color: #888; }
            QScrollArea { border: none; background-color: #121212; }
            QWidget { background-color: #121212; color: #e0e0e0; }
        """)
        
        self.db = DBManager()
        
        # Ensure cache directory exists
        self.cache_dir = os.path.join(config.BASE_DIR, "data", "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        
        # --- FIX: Initialize Placeholders ---
        self.details_page = QWidget()
        self.list_page = QWidget()
        self.central_stack.addWidget(self.details_page)
        self.central_stack.addWidget(self.list_page)
        
        # Pages
        self.home_page = None # Lazy load
        self.refresh_home()


    def get_cached_image(self, url, card_id):
        if not url: return None
        ext = url.split('.')[-1].split('?')[0]
        filename = f"{card_id}.{ext}"
        local_path = os.path.join(self.cache_dir, filename)
        if os.path.exists(local_path): return local_path
        try:
            print(f"Downloading cache: {url}")
            response = requests.get(url, headers={"User-Agent": config.API_USER_AGENT})
            if response.status_code == 200:
                with open(local_path, 'wb') as f: f.write(response.content)
                return local_path
        except: pass
        return None

    def refresh_home(self):
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
        
        # Charts Row
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)
        
        # Color Chart
        if self.stats['colors']:
            chart_col = self.create_chart_frame(self.stats['colors'], "Mana Colors", "color")
            charts_layout.addWidget(chart_col)
            
        # Rarity Chart (NEW)
        if self.stats['rarity']:
            chart_rar = self.create_chart_frame(self.stats['rarity'], "Rarity", "rarity")
            charts_layout.addWidget(chart_rar)
            
        layout.addLayout(charts_layout, stretch=1)
        
        # Gallery
        gallery = self.create_recent_gallery()
        layout.addWidget(gallery)
        
        return page

    def create_stats_header(self, stats):
        frame = QFrame()
        frame.setStyleSheet("background-color: #1e1e1e; border-bottom: 2px solid #333;")
        layout = QHBoxLayout(frame)
        
        def add_box(title, val, color="#fff"):
            v = QVBoxLayout()
            t = QLabel(title.upper())
            t.setStyleSheet("color: #888; font-size: 11px; letter-spacing: 1px;")
            l = QLabel(str(val))
            l.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 800;")
            v.addWidget(t)
            v.addWidget(l)
            layout.addLayout(v)

        add_box("Cards", stats['total_count'])
        add_box("Collection Value", f"${stats['total_value']}", config.PRICE_ALERTS["rare"]["color"])
        
        if stats['top_card']:
            tc = stats['top_card']
            # Leaderboard Button
            btn = QPushButton(f"👑  Top Card: {tc['display_name']} (${tc['price_usd']})")
            btn.setStyleSheet("""
                background-color: #2a2100; 
                color: #FFD700; 
                border: 1px solid #665200; 
                font-size: 16px; 
                padding: 10px 20px;
            """)
            btn.setCursor(Qt.PointingHandCursor)
            # Click -> Show All sorted by Price
            btn.clicked.connect(lambda: self.show_list("all", "All Cards (Leaderboard)"))
            layout.addStretch()
            layout.addWidget(btn)
            
        return frame

    def create_chart_frame(self, data, title, filter_type):
        frame = QFrame()
        frame.setStyleSheet("background-color: #2d2d2d; border-radius: 12px;")
        layout = QVBoxLayout(frame)
        
        canvas = FigureCanvas(Figure(figsize=(4, 4), facecolor='#2d2d2d'))
        ax = canvas.figure.add_subplot(111)
        
        labels = list(data.keys())
        values = list(data.values())
        
        # Color Palettes
        if filter_type == "color":
            cmap = {"W": "#F0E6BC", "U": "#4169E1", "B": "#A9A9A9", "R": "#F08080", "G": "#228B22", "Multi": "#FFD700", "Colorless": "#C0C0C0"}
            colors = [cmap.get(l, "#fff") for l in labels]
        else: # Rarity
            cmap = {"common": "#ffffff", "uncommon": "#b0c3d9", "rare": "#d4af37", "mythic": "#ff8000"}
            colors = [cmap.get(l, "#777") for l in labels]

        wedges, _, _ = ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=45)
        
        # Style
        ax.set_title(title, color='white', pad=10)
        for text in ax.texts: text.set_color('white')
        
        # Interaction
        def on_pick(event):
            if event.artist in wedges:
                idx = wedges.index(event.artist)
                self.show_list(filter_type, labels[idx])

        for w in wedges: w.set_picker(True)
        canvas.figure.canvas.mpl_connect('pick_event', on_pick)
        
        layout.addWidget(canvas)
        return frame

    def create_recent_gallery(self):
        # ... (Same as before but maybe ensure background is clean) ...
        # Can copy previous code here, logic is unchanged.
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.addWidget(QLabel("Recently Scanned"))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        h_layout = QHBoxLayout(content)
        h_layout.setAlignment(Qt.AlignLeft)
        
        scans = self.db.get_recent_scans(8)
        for card in scans:
            btn = QPushButton()
            btn.setFixedSize(130, 200)
            btn.setStyleSheet("border: none; background: transparent;")
            btn.setCursor(Qt.PointingHandCursor)
            
            v = QVBoxLayout(btn)
            v.setSpacing(5)
            
            img = QLabel()
            if card['local_image_path'] and os.path.exists(card['local_image_path']):
                pix = QPixmap(card['local_image_path']).scaled(120, 168, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img.setPixmap(pix)
            
            p_val = card['price_usd']
            color = "#fff"
            if p_val and float(p_val) > 1.0: color = config.PRICE_ALERTS['uncommon']['color']
            
            lbl = QLabel(f"${p_val}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            v.addWidget(img)
            v.addWidget(lbl)
            
            btn.clicked.connect(lambda checked=False, tid=card['tracker_id']: self.show_details(tid))
            h_layout.addWidget(btn)
            
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return frame

    # --- LIST PAGE ---
    def show_list(self, filter_type, filter_value):
        cards = self.db.get_cards_by_filter(filter_type, filter_value, limit=200)
        
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Top Bar
        top = QHBoxLayout()
        back = QPushButton("← Dashboard")
        back.setFixedSize(120, 40)
        back.clicked.connect(self.refresh_home)
        
        title_text = f"Filter: {filter_value.title()}" if filter_type != "all" else filter_value
        lbl = QLabel(title_text)
        lbl.setStyleSheet("font-size: 24px; font-weight: bold; margin-left: 20px;")
        
        top.addWidget(back)
        top.addWidget(lbl)
        top.addStretch()
        layout.addLayout(top)
        
        # Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(15)
        
        row, col = 0, 0
        for card in cards:
            # Card Wrapper
            wrapper = QFrame()
            wrapper.setFixedSize(180, 280)
            wrapper.setStyleSheet("background-color: #252525; border-radius: 8px; border: 1px solid #333;")
            
            v = QVBoxLayout(wrapper)
            v.setContentsMargins(10,10,10,10)
            
            # Image (Use Local scan for speed)
            img_lbl = QLabel()
            path = card['local_image_path']
            if path and os.path.exists(path):
                pix = QPixmap(path).scaled(160, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_lbl.setPixmap(pix)
            else:
                img_lbl.setText("No Image")
                img_lbl.setAlignment(Qt.AlignCenter)
            
            # Price
            p_val = card['price_usd']
            p_str = f"${p_val}" if p_val else "N/A"
            
            # Color logic based on config
            p_color = config.PRICE_ALERTS['bulk']['color']
            if p_val:
                pv = float(p_val)
                if pv >= config.PRICE_ALERTS['mythic']['min']: p_color = config.PRICE_ALERTS['mythic']['color']
                elif pv >= config.PRICE_ALERTS['rare']['min']: p_color = config.PRICE_ALERTS['rare']['color']
                elif pv >= config.PRICE_ALERTS['uncommon']['min']: p_color = config.PRICE_ALERTS['uncommon']['color']
            
            price_lbl = QLabel(p_str)
            price_lbl.setAlignment(Qt.AlignCenter)
            price_lbl.setStyleSheet(f"color: {p_color}; font-weight: bold; font-size: 14px;")
            
            v.addWidget(img_lbl)
            v.addWidget(price_lbl)
            
            # Interaction
            btn = QPushButton(wrapper)
            btn.setGeometry(0, 0, 180, 280)
            btn.setStyleSheet("background: transparent; border: none;")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, tid=card['tracker_id']: self.show_details(tid))
            
            grid.addWidget(wrapper, row, col)
            col += 1
            if col > 5: # 6 columns
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
        
        # --- 1. NAVBAR ---
        nav = QHBoxLayout()
        back = QPushButton("← HOME")
        back.setFixedSize(100, 35)
        back.clicked.connect(self.refresh_home)
        
        del_btn = QPushButton("🗑️ Remove Card")
        del_btn.setFixedSize(120, 35)
        del_btn.setStyleSheet("background-color: #3a0000; color: #ffcccc; border: 1px solid #ff4444;")
        del_btn.clicked.connect(lambda: self.delete_card(tracker_id, card['display_name']))
        
        nav.addWidget(back)
        nav.addStretch()
        nav.addWidget(del_btn)
        layout.addLayout(nav)
        
        # --- 2. MAIN CONTENT ---
        content = QHBoxLayout()
        content.setSpacing(40) # More breathing room
        
        # --- LEFT COLUMN: IMAGES & DATES ---
        # imgs col should be horizontal box with two vertical boxes inside
        imgs_row = QHBoxLayout()
        imgs_col1 = QVBoxLayout()
        imgs_col2 = QVBoxLayout()
        imgs_col1.setAlignment(Qt.AlignTop)
        imgs_col2.setAlignment(Qt.AlignTop)

        # > SCAN SECTION
        scan_lbl_header = QLabel("YOUR SCAN")
        scan_lbl_header.setAlignment(Qt.AlignCenter)
        scan_lbl_header.setStyleSheet("color: #888; font-size: 11px; letter-spacing: 2px; font-weight: bold;")
        imgs_col1.addWidget(scan_lbl_header)
        
        scan_img = QLabel()
        scan_img.setFixedSize(300, 420)
        scan_img.setStyleSheet("background-color: #050505; border: 1px solid #333; border-radius: 8px;")
        scan_img.setAlignment(Qt.AlignCenter)
        if card['local_image_path'] and os.path.exists(card['local_image_path']):
            pix = QPixmap(card['local_image_path']).scaled(300, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            scan_img.setPixmap(pix)
        imgs_col1.addWidget(scan_img)
        
        # Scan Date
        scan_date_raw = card['date_scanned'] # 2025-11-29T16:39...
        scan_date_fmt = scan_date_raw.split('T')[0]
        scan_meta = QLabel(f"Scanned: {scan_date_fmt}")
        scan_meta.setAlignment(Qt.AlignCenter)
        scan_meta.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 20px;")
        imgs_col1.addWidget(scan_meta)

        # > OFFICIAL ART SECTION
        web_lbl_header = QLabel("OFFICIAL ART")
        web_lbl_header.setAlignment(Qt.AlignCenter)
        web_lbl_header.setStyleSheet("color: #888; font-size: 11px; letter-spacing: 2px; font-weight: bold;")
        imgs_col2.addWidget(web_lbl_header)
        
        web_img = QLabel("Downloading...")
        web_img.setFixedSize(300, 420)
        web_img.setStyleSheet("background-color: #050505; border: 1px solid #333; border-radius: 8px;")
        web_img.setAlignment(Qt.AlignCenter)
        
        web_path = self.get_cached_image(card['image_url'], card['scryfall_id'])
        if web_path:
            pix = QPixmap(web_path).scaled(300, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            web_img.setPixmap(pix)
            web_img.setText("")
        else:
            web_img.setText("No Image Available")
        imgs_col2.addWidget(web_img)
        
        # Artist & Release Date
        artist = card.get('artist', 'Unknown Artist')
        release = card.get('released_at', 'Unknown Date')
        web_meta = QLabel(f"Illus. {artist} • Released {release}")
        web_meta.setAlignment(Qt.AlignCenter)
        web_meta.setStyleSheet("color: #666; font-size: 11px;")
        imgs_col2.addWidget(web_meta)
        
        imgs_col2.addStretch()

        imgs_row.addLayout(imgs_col1)
        imgs_row.addLayout(imgs_col2)

        content.addLayout(imgs_row)
                
        # --- RIGHT COLUMN: DATA SHEET ---
        info_col = QVBoxLayout()
        info_col.setAlignment(Qt.AlignTop)
        
        # Header
        name = QLabel(card['display_name'])
        name.setStyleSheet("font-size: 38px; font-weight: 800; color: white; margin-top: 10px;")
        name.setWordWrap(True)
        info_col.addWidget(name)
        
        # Set / Rarity
        set_info = f"{card['set_name']} ({card['set_code'].upper()}) #{card['collector_number']}"
        rarity = card['rarity'].title()
        meta = QLabel(f"{set_info}  •  {rarity}")
        meta.setStyleSheet("font-size: 16px; color: #bbb; margin-bottom: 20px;")
        info_col.addWidget(meta)
        
        # Price Block
        p_val = card['price_usd']
        p_col = config.PRICE_ALERTS['bulk']['color']
        if p_val:
            pv = float(p_val)
            if pv >= config.PRICE_ALERTS['mythic']['min']: p_col = config.PRICE_ALERTS['mythic']['color']
            elif pv >= config.PRICE_ALERTS['rare']['min']: p_col = config.PRICE_ALERTS['rare']['color']
            elif pv >= config.PRICE_ALERTS['uncommon']['min']: p_col = config.PRICE_ALERTS['uncommon']['color']
            elif pv >= config.PRICE_ALERTS['common']['min']: p_col = config.PRICE_ALERTS['common']['color']
            
        price_row = QHBoxLayout()
        price_lbl = QLabel(f"${p_val} USD")
        price_lbl.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {p_col};")
        price_row.addWidget(price_lbl)
        
        if card['price_foil']:
            foil_lbl = QLabel(f"(Foil: ${card['price_foil']})")
            foil_lbl.setStyleSheet("color: #666; font-size: 16px; margin-left: 10px; margin-top: 10px;")
            price_row.addWidget(foil_lbl)
        price_row.addStretch()
        info_col.addLayout(price_row)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #333; margin-top: 10px; margin-bottom: 20px;")
        info_col.addWidget(line)
        
        # Oracle Box
        oracle_frame = QFrame()
        oracle_frame.setStyleSheet("""
            background-color: #252525; 
            border: 1px solid #333;
            border-left: 4px solid #555; 
            border-radius: 6px;
            padding: 20px;
        """)
        o_layout = QVBoxLayout(oracle_frame)
        o_layout.setSpacing(15)
        
        # Type Line
        type_line = QLabel(card['type_line'])
        type_line.setStyleSheet("font-weight: bold; font-size: 15px; color: #fff;")
        o_layout.addWidget(type_line)
        
        # Rules Text
        if card['oracle_text']:
            o_text = QLabel(card['oracle_text'])
            o_text.setWordWrap(True)
            o_text.setStyleSheet("font-size: 15px; line-height: 1.6; color: #e0e0e0;")
            o_layout.addWidget(o_text)
            
        # Flavor Text (New)
        if card['flavor_text']:
            f_text = QLabel(card['flavor_text'])
            f_text.setWordWrap(True)
            f_text.setStyleSheet("font-size: 13px; font-style: italic; color: #888; margin-top: 5px;")
            o_layout.addWidget(f_text)
        
        # Stats / Mana
        stats_row = QHBoxLayout()
        if card['power'] and card['toughness']:
            pt = QLabel(f"{card['power']} / {card['toughness']}")
            pt.setStyleSheet("font-size: 18px; font-weight: bold; background-color: #111; padding: 5px 10px; border-radius: 4px; border: 1px solid #444;")
            stats_row.addWidget(pt)
            
        if card['mana_cost']:
            mana = QLabel(f"Mana: {card['mana_cost']} (CMC {card['cmc']})")
            mana.setStyleSheet("color: #aaa; font-size: 13px;")
            stats_row.addWidget(mana)
            
        stats_row.addStretch()
        o_layout.addLayout(stats_row)
            
        info_col.addWidget(oracle_frame)
        info_col.addStretch()
        
        content.addLayout(info_col, stretch=2)
        layout.addLayout(content)
        
        # Wrap content in a scroll area for the details page itself
        # (Useful if the card has massive text or small screen)
        outer_scroll = QScrollArea()
        outer_scroll.setWidgetResizable(True)
        outer_page_container = QWidget()
        outer_page_container.setLayout(layout)
        outer_scroll.setWidget(outer_page_container)
        
        # We need to add the scroll to the stacked widget, not the page directly
        # But our structure expects widgets.
        # Let's just set the layout to the page we return.
        
        self.central_stack.removeWidget(self.details_page)
        self.details_page = outer_scroll # Use scroll area as the page
        self.central_stack.addWidget(self.details_page)
        self.central_stack.setCurrentWidget(self.details_page)

    def delete_card(self, tracker_id, name):
        reply = QMessageBox.question(self, 'Delete Card?', 
                                     f"Permanently remove '{name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_scan(tracker_id)
            self.refresh_home()