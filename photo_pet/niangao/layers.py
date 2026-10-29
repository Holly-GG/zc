"""Independent artwork layers; controls and text always stay in Qt layouts."""
from functools import lru_cache
from PySide6.QtGui import QPixmap
from .art import asset_path

@lru_cache(maxsize=32)
def layer(name):
    return QPixmap(str(asset_path('ui/layers/'+name+'.png')))
