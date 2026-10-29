"""One QSS design system: readable controls over illustrated botanical stationery."""
from string import Template
from .typography import stylesheet_tokens
TOKENS={'ink':'#2A472F','forest':'#3C582C','olive':'#839D45','sage':'#92AB76',
 'vellum':'#E8E9C0','blue':'#77AAD7','sky':'#B4D3EC','paper':'#F5F2E4','card':'#FCFAF0',
 'line':'#B9AE7A','muted':'#66745C','focus':'#3E7197','error':'#8D4136'}
STATE_COLORS={'satiety':TOKENS['sage'],'cleanliness':TOKENS['blue'],'energy':'#CBAA57','mood':'#C98D88','health':'#5C947A'}
STYLE=Template('''
QWidget {color:${ink};font-family:"${body_font}";font-size:${body_size}px;}
QMainWindow,QWidget#lifeRoot {background:${paper};}
QLabel {background:transparent;}
QLabel#hero {font-family:"${title_font}";font-size:${title_size}px;font-weight:600;}
QLabel#brand {font-family:"${title_font}";font-size:18px;font-weight:600;}
QLabel#scriptTitle {font-family:"${script_font}";font-size:${script_size}px;color:#5A807F;}
QLabel#sectionTitle {font-family:"${title_font}";font-size:17px;font-weight:600;}
QLabel#sub {color:${muted};font-size:12px;}
QLabel#sub[severity="error"] {color:${error};}
QLabel#sub[severity="warning"] {color:#7A5A31;}
QLabel#eyebrow {color:${muted};font-size:11px;letter-spacing:.5px;}
QLabel#chip {background:${vellum};padding:5px 9px;border-radius:10px;color:${forest};}
QLabel#candidate {color:#716A54;font-size:11px;background:#F2EDD9;padding:3px 6px;border-radius:5px;}
QLabel#emptyState {background:${card};border:1px dashed ${line};border-radius:8px;padding:22px;color:${muted};}
QFrame#header {background:#FAF7E9;border:1px solid ${line};border-top:2px solid ${olive};border-radius:7px;}
QFrame#sidebar {background:#ECEED7;border:1px solid #A8B180;border-radius:7px;}
QListWidget#navigation {background:transparent;border:0;padding:0;outline:none;}
QListWidget#navigation::item {padding:9px 5px;margin:2px 0;border-bottom:1px solid #D1D7B9;min-height:19px;}
QListWidget#navigation::item:hover {background:#F4F4E4;border-radius:7px;}
QListWidget#navigation::item:selected {background:#DCE3C5;border-left:3px solid ${forest};border-radius:7px;color:${ink};font-weight:600;}
QFrame#paperCard,QFrame#itemCard,QFrame#photoCard {background:#FCF8E9;border:1px solid ${line};border-radius:8px;}
QFrame#itemCard:hover,QFrame#photoCard:hover {background:#F1F3DF;border-color:${olive};}
QLabel#productName {font-family:"${title_font}";font-size:15px;font-weight:600;}
QLabel#productDetail {font-size:12px;color:${muted};}
QPushButton {background:#EDF0DA;color:${ink};border:1px solid #9FAF7C;border-bottom:2px solid #8B9D6C;border-radius:6px;padding:7px 11px;font-weight:500;}
QPushButton:hover {background:${vellum};border-color:${forest};}
QPushButton:pressed {background:#DCE3C5;}
QPushButton:focus {border:2px solid ${focus};}
QPushButton#primary:focus,QPushButton#quiet:focus,QPushButton#danger:focus,QFrame#itemCard:focus {border:2px solid ${focus};}
QPushButton:disabled {background:#ECECE2;color:#6D7467;border-color:#C5C9B5;}
QPushButton#primary {background:${forest};color:${card};border-color:${forest};}
QPushButton#primary:hover {background:${ink};color:${card};}
QPushButton#primary:disabled {background:#ECECE2;color:#6D7467;border-color:#C5C9B5;}
QPushButton#quiet {background:${card};padding:5px 9px;border:1px solid #ADB98C;}
QPushButton#danger {background:${card};color:${error};border-color:${error};}
QPushButton#danger:hover {background:#F5EAE4;}
QPushButton#photoPreview {background:#F5F1DE;border:1px solid #D6C9A4;border-radius:2px;padding:2px;}
QLineEdit,QTextEdit,QTextBrowser,QSpinBox,QDoubleSpinBox,QComboBox,QDateEdit {background:#FFFDF5;border:1px solid #B7C29D;border-radius:6px;padding:7px;selection-background-color:${sky};selection-color:${ink};}
QLineEdit:focus,QTextEdit:focus,QComboBox:focus,QSpinBox:focus,QDateEdit:focus {border:2px solid ${focus};}
QLineEdit:disabled,QComboBox:disabled,QDateEdit:disabled {background:#ECECE2;color:#6D7467;}
QTextBrowser {padding:10px;}
QListWidget {background:#FFFDF5;border:1px solid #B7C29D;border-radius:7px;padding:4px;outline:none;}
QListWidget::item {padding:8px 6px;margin:2px;}
QListWidget::item:selected {background:${vellum};color:${ink};border-radius:5px;}
QGroupBox {background:#FCF9EC;border:1px solid ${line};border-radius:8px;margin-top:18px;padding:14px;}
QGroupBox::title {subcontrol-origin:margin;left:14px;padding:0 6px;background:${paper};font-family:"${title_font}";font-size:16px;font-weight:600;}
QProgressBar {background:#E0E5CC;border:1px solid #BCC5A1;border-radius:5px;min-height:14px;text-align:center;font-size:11px;}
QProgressBar::chunk {background:#A4CAB8;border-radius:4px;}
QTabWidget::pane {background:${card};border:1px solid #B7C29D;border-radius:6px;}
QTabBar::tab {background:#E9EED8;color:${forest};border:1px solid #B7C29D;padding:7px 12px;margin-right:3px;border-top-left-radius:6px;border-top-right-radius:6px;}
QTabBar::tab:selected {background:${card};color:${ink};font-weight:600;border-top:2px solid ${olive};}
QWidget#workTabPage {background:${card};}
QLabel#focusClock {font-family:"${title_font}";font-size:38px;color:${ink};letter-spacing:2px;}
QCheckBox {padding:4px;}
QScrollArea {border:0;background:transparent;}
QScrollBar:vertical {width:8px;background:transparent;margin:3px;}
QScrollBar::handle:vertical {background:#BDCEA5;border-radius:4px;min-height:30px;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}
QMenu {background:${card};color:${ink};border:1px solid ${olive};padding:6px;}
QMenu::item {padding:7px 15px;} QMenu::item:selected {background:${vellum};}
''').substitute(TOKENS|stylesheet_tokens())

def chapter_style(chapter):
    return f"QGroupBox::title {{background:{chapter['paper']};}} QFrame#itemCard {{border-top:2px solid {chapter['accent']};}}"
