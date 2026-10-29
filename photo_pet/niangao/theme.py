"""Niangao's cream stationery palette, shared by desktop cards and dashboard."""
STYLE='''
QMainWindow,QWidget#lifeRoot {background:#fbf7ef;color:#384d49;}
QWidget {color:#384d49;font-size:13px;}
QLabel {background:transparent;} QLabel#hero {font-size:23px;font-weight:700;color:#305e63;}
QLabel#sub {color:#7e8d80;font-size:12px;} QLabel#eyebrow {color:#7b8f77;font-size:11px;font-weight:700;}
QLabel#brand {font-size:17px;font-weight:700;color:#305e63;} QLabel#chip {background:#e4efe7;color:#507669;border-radius:9px;padding:5px 9px;}
QFrame#sidebar {background:#e3ede1;border:1px solid #bfceba;border-radius:18px;}
QFrame#header {background:#fffdf7;border:1px solid #d9ddca;border-radius:14px;}
QPushButton {background:#cce2d1;border:1.4px solid #789580;border-radius:10px;padding:8px 11px;font-weight:600;}
QPushButton:hover {background:#f8e4ad;border-color:#b9a37a;} QPushButton:pressed {background:#efc9c0;}
QPushButton:disabled {background:#ecece2;color:#a6aaa0;border-color:#d3d7ca;}
QPushButton#quiet {background:#fffaf0;border:1px solid #c6d5c6;padding:5px 9px;}
QLineEdit,QTextEdit,QTextBrowser,QSpinBox,QDoubleSpinBox,QComboBox,QDateEdit {background:#fffefa;border:1px solid #c7d3c5;border-radius:9px;padding:7px;selection-background-color:#cce2d1;}
QLineEdit:focus,QTextEdit:focus {border:1.5px solid #6ba38e;}
QListWidget {outline:none;background:#fffefa;border:1px solid #c7d3c5;border-radius:11px;padding:4px;}
QListWidget::item {padding:8px 7px;margin:2px;} QListWidget::item:selected {background:#f7e4ac;border-radius:8px;color:#305e63;}
QListWidget#navigation {background:transparent;border:0;} QListWidget#navigation::item {padding:8px 6px;margin:3px 0;}
QListWidget#navigation::item:hover {background:#f5f8eb;border-radius:9px;}
QListWidget#navigation::item:selected {background:#fffaf0;color:#305e63;border-left:3px solid #75a68f;border-radius:9px;font-weight:700;}
QGroupBox {background:#fffdf7;border:1px solid #c7d3c5;border-radius:14px;margin-top:16px;padding:13px;}
QGroupBox::title {subcontrol-origin:margin;left:14px;padding:0 6px;background:#fbf7ef;font-weight:600;color:#537d6e;}
QFrame#itemCard {background:#fffdf7;border:1px solid #c7d3c5;border-radius:16px;}
QFrame#itemCard:hover {background:#f4f6e9;border:1.5px solid #8cae97;}
QLabel#productName {font-weight:700;color:#305e63;}
QLabel#productDetail {font-size:11px;color:#7e8d80;}
QProgressBar {background:#e6ede2;border:0;border-radius:6px;min-height:14px;text-align:center;color:#3e655a;font-size:10px;}
QProgressBar::chunk {background:#a9ceb7;border-radius:6px;}
QTabWidget::pane {background:#fffdf7;border:1px solid #c7d3c5;border-radius:10px;}
QTabBar::tab {background:#e3ede1;color:#507669;border:1px solid #c7d3c5;padding:7px 13px;margin-right:3px;border-top-left-radius:7px;border-top-right-radius:7px;}
QTabBar::tab:selected {background:#fffdf7;color:#305e63;font-weight:700;}
QWidget#workTabPage {background:#fffdf7;}
QCheckBox {padding:4px;} QScrollArea {border:0;background:transparent;}
QScrollBar:vertical {width:8px;background:transparent;margin:3px;}
QScrollBar::handle:vertical {background:#c4d7c3;border-radius:4px;min-height:30px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}
'''
