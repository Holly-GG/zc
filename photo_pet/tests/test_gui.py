import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint,Qt
from PySide6.QtTest import QTest
from niangao.art import CatArt
from niangao.config import Settings
from niangao.pet import PetWindow

@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])

@pytest.fixture(scope='module')
def art(app):return CatArt()

def test_all_assets_have_real_alpha_and_walking_frames(art):
    assert len(art.frames['walk'])==4
    for frames in art.frames.values():
        for frame in frames:assert frame.hasAlphaChannel() and not frame.isNull()
    assert len({bytes(f.constBits()) for f in art.frames['walk']})==4

def test_input_region_is_not_bounding_rectangle(art):
    image,mask=art.render('idle',0,240,312)
    from PySide6.QtGui import QRegion
    region=QRegion(mask)
    assert not region.isEmpty()
    assert not region.contains(QPoint(0,0))
    assert region.contains(QPoint(120,170))
    # There must be transparent points inside the outer bounding rectangle.
    bounds=region.boundingRect()
    assert any(not region.contains(QPoint(x,y)) for x in range(bounds.left(),bounds.right(),8) for y in range(bounds.top(),bounds.bottom(),8))

def test_pet_interactions_and_persistence(app,tmp_path,art):
    pet=PetWindow(Settings(tmp_path/'settings.json'))
    pet.show();app.processEvents()
    assert pet.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert pet.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    pet.feed();assert pet.behaviour.state=='feed' and pet.counts['fed']==1
    pet.pet_head();assert pet.behaviour.state=='pet'
    pet.toggle_sleep();assert pet.behaviour.state=='sleep'
    pet.toggle_sleep();assert pet.behaviour.state=='idle'
    old=pet.width();pet.resize_pet(280);assert pet.width()!=old
    pet.toggle_top();assert not pet.settings.data['always_on_top']
    QTest.mouseClick(pet,Qt.MouseButton.LeftButton,pos=QPoint(130,170))
    assert pet.counts['clicked']==1
    if pet.bubble.isVisible():
        assert not pet.geometry().intersects(pet.bubble.geometry())
    pet.close();app.processEvents()
    assert Settings(tmp_path/'settings.json').data['width']==280
