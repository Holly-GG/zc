"""Qt QSS design tokens (Qt does not implement browser CSS custom properties)."""
TOKENS={
 'ink':'#2A472F','forest':'#3C582C','olive':'#839D45','sage':'#92AB76',
 'vellum':'#E8E9C0','blue':'#77AAD7','sky':'#B4D3EC',
 'paper':'#F5F2E4','card':'#FCFAF0','line':'#B7BE94','muted':'#66745C',
}

from string import Template
STYLE='''
QMainWindow,QWidget#lifeRoot {background:${paper};color:${ink};}
QWidget {color:${ink};font-size:13px;}
QLabel {background:transparent;} QLabel#hero {font-size:23px;font-weight:700;color:${ink};}
QLabel#sub {color:${muted};font-size:12px;} QLabel#eyebrow {color:${forest};font-size:11px;font-weight:700;}
QLabel#brand {font-size:17px;font-weight:700;color:${ink};} QLabel#chip {background:${vellum};color:${forest};border-radius:9px;padding:5px 9px;}
QFrame#sidebar {background:${vellum};border:1px solid ${sage};border-radius:18px;}
QFrame#header {background:${card};border:1px solid ${line};border-radius:14px;}
QPushButton {background:#DCE3C5;border:1.4px solid ${olive};border-radius:10px;padding:8px 11px;font-weight:600;}
QPushButton:hover {background:${vellum};border-color:${forest};} QPushButton:pressed {background:${sky};}
QPushButton:disabled {background:#ecece2;color:#a6aaa0;border-color:#d3d7ca;}
QPushButton#quiet {background:#fffaf0;border:1px solid ${line};padding:5px 9px;}
QLineEdit,QTextEdit,QTextBrowser,QSpinBox,QDoubleSpinBox,QComboBox,QDateEdit {background:#fffefa;border:1px solid ${line};border-radius:9px;padding:7px;selection-background-color:#DCE3C5;}
QLineEdit:focus,QTextEdit:focus {border:1.5px solid ${blue};}
QListWidget {outline:none;background:#fffefa;border:1px solid ${line};border-radius:11px;padding:4px;}
QListWidget::item {padding:8px 7px;margin:2px;} QListWidget::item:selected {background:${vellum};border-radius:8px;color:${ink};}
QListWidget#navigation {background:transparent;border:0;} QListWidget#navigation::item {padding:8px 6px;margin:3px 0;}
QListWidget#navigation::item:hover {background:#f5f8eb;border-radius:9px;}
QListWidget#navigation::item:selected {background:#fffaf0;color:${ink};border-left:3px solid ${olive};border-radius:9px;font-weight:700;}
QGroupBox {background:${card};border:1px solid ${line};border-radius:14px;margin-top:16px;padding:13px;}
QGroupBox::title {subcontrol-origin:margin;left:14px;padding:0 6px;background:${paper};font-weight:600;color:${forest};}
QFrame#itemCard {background:${card};border:1px solid ${line};border-radius:16px;}
QFrame#itemCard:hover {background:#f4f6e9;border:1.5px solid ${olive};}
QLabel#productName {font-weight:700;color:${ink};}
QLabel#productDetail {font-size:11px;color:${muted};}
QProgressBar {background:#e6ede2;border:0;border-radius:6px;min-height:14px;text-align:center;color:#3e655a;font-size:10px;}
QProgressBar::chunk {background:${sage};border-radius:6px;}
QTabWidget::pane {background:${card};border:1px solid ${line};border-radius:10px;}
QTabBar::tab {background:${vellum};color:${forest};border:1px solid ${line};padding:7px 13px;margin-right:3px;border-top-left-radius:7px;border-top-right-radius:7px;}
QTabBar::tab:selected {background:${card};color:${ink};font-weight:700;}
QWidget#workTabPage {background:${card};}
QCheckBox {padding:4px;} QScrollArea {border:0;background:transparent;}
QScrollBar:vertical {width:8px;background:transparent;margin:3px;}
QScrollBar::handle:vertical {background:${sage};border-radius:4px;min-height:30px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}
'''

# Reusable paper, letter, card and herbarium rules; no metrics change input behaviour.
STYLE += """
QLabel#hero {font-size:22px;font-weight:600;letter-spacing:1px;}
QLabel#eyebrow {font-size:10px;letter-spacing:1px;}
QLabel#brand {font-size:17px;letter-spacing:1px;}
QFrame#header {border-radius:4px;border-top:3px solid ${forest};border-bottom:1px solid ${olive};}
QFrame#sidebar {border-radius:5px;border:1px solid ${olive};}
QListWidget#navigation::item {padding:9px 5px;margin:3px 0;border-bottom:1px solid #CAD0AD;}
QListWidget#navigation::item:selected {border-radius:3px;background:${card};border-left:3px solid ${forest};}
QPushButton {border-radius:5px;border-bottom:2px solid ${olive};}
QPushButton#quiet {border-radius:4px;background:#F7F5E7;}
QLineEdit,QTextEdit,QTextBrowser,QSpinBox,QDoubleSpinBox,QComboBox,QDateEdit {border-radius:5px;}
QTextBrowser {padding:10px;line-height:1.5;}
QLineEdit:focus,QTextEdit:focus,QComboBox:focus,QSpinBox:focus {border:1.5px solid ${blue};}
QGroupBox {border-radius:4px;border-top:2px solid ${sage};}
QGroupBox::title {background:${paper};}
QFrame#itemCard {border-radius:4px;border-top:2px solid ${sage};background:${card};}
QFrame#itemCard:hover {background:#F2F4E4;border-color:${olive};}
QProgressBar {border:1px solid ${line};border-radius:3px;background:#E9EDDC;}
QProgressBar::chunk {border-radius:2px;background:${sage};}
QTabWidget::pane {border-radius:4px;}
QMenu {background:${card};color:${ink};border:1px solid ${olive};padding:6px;}
QMenu::item {padding:6px 15px;} QMenu::item:selected {background:${vellum};}
"""

STYLE += """
QPushButton#careAction {background:#FCF7E6;border:1px solid #B9AE7A;min-height:44px;}
QPushButton#careAction:hover {background:#E8E9C0;border-color:${olive};}
QLabel#focusClock {font-size:34px;color:${ink};font-weight:500;letter-spacing:2px;}
QFrame#header {background:#F8F4DF;border-top:2px solid ${olive};border-radius:5px;}
QFrame#sidebar {background:#EEEDCF;border:1px solid #ACA66D;}
QFrame#itemCard {background:#FCF7E6;border:1px solid #B9AE7A;border-radius:7px;}
QFrame#itemCard:hover {background:#F3F1D6;border-color:${olive};}
QPushButton {background:#CFDAB7;border-color:#9AAB76;border-bottom:2px solid #879A68;}
QPushButton:pressed {background:${sky};}
QPushButton#quiet {background:#F8F4DF;}
QProgressBar {background:#E0E5CC;border-color:#BCC5A1;}
QGroupBox {background:#FCF8E8;border-color:#B9AE7A;}
"""

STYLE=Template(STYLE).substitute(TOKENS)

def chapter_style(chapter):
    """Scoped palette, retaining shared widget sizes and semantics."""
    return (f"QWidget#journalPage {{color:{TOKENS['ink']};}} "
            f"QGroupBox::title {{background:{chapter['paper']};color:{chapter['accent']};}} "
            f"QProgressBar::chunk {{background:{chapter['wash']};}} "
            f"QFrame#itemCard {{border-top-color:{chapter['accent']};}}")
