import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread
from PySide6.QtTest import QTest
from niangao.config import Settings
from niangao.pet import PetWindow
from niangao.life.jobs import run_job
def test_dashboard_real_buttons_and_assets(tmp_path):
    app=QApplication.instance() or QApplication([])
    pet=PetWindow(Settings(tmp_path/"settings.json"));pet.open_life();ui=pet.life_window
    assert ui.stack.count()==8
    for i in range(8):ui.nav.setCurrentRow(i);app.processEvents()
    for action in ("groom","stretch","feed","pet","play_bow","yawn"):
        assert pet.perform_action(action);assert len(pet.art.frames[action])==4
        assert len({(f.width(),f.height()) for f in pet.art.frames[action]})==1
        pix,mask=pet.art.render(action,2,240,312);assert not mask.isNull()
    assert not pet.perform_action("nonexistent")
    ui.care("brush","groom");assert pet.behaviour.state=="groom"
    ui.task_input.setText("完成一次测试");ui.add_task();assert ui.tasks.count()==1
    ui.generate_diary();assert "梳理" in ui.diary_text.toPlainText()
    assert not any("3D" in ui.nav.item(i).text() for i in range(ui.nav.count()))
    assert ui.nav.item(2).text()=="年糕小铺" and ui.nav.item(3).text()=="我的背包"
    ui.place_or_use("bed");assert any(w.id=="bed" for w in pet.desktop.widgets.values())
    pet.desktop.clear();assert not pet.desktop.widgets
    ui.chat_input.setText("小棕点");ui.send_chat();assert "本地回应" in ui.chat_log.toPlainText();assert pet.life.data["badges"]
    pet.close();app.processEvents()
def test_background_result_runs_on_gui_thread():
    app=QApplication.instance() or QApplication([]);results=[]
    run_job(lambda:"ok",lambda value:results.append((value,QThread.currentThread())),lambda err:results.append(err))
    for _ in range(100):
        QTest.qWait(10)
        if results:break
    assert results and results[0][0]=="ok" and results[0][1]==app.thread()
