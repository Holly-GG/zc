"""Windows single-file entry point; also supports Linux development."""
import argparse,sys,traceback,os
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--settings",type=Path)
    parser.add_argument("--probe",type=Path)
    parser.add_argument("--smoke",action="store_true")
    parser.add_argument("--suite-smoke",action="store_true")
    parser.add_argument("--motion-smoke",action="store_true")
    parser.add_argument("--desktop-smoke",action="store_true")
    parser.add_argument("--expanded-smoke",action="store_true")
    args=parser.parse_args()
    if args.probe:args.probe.parent.mkdir(parents=True,exist_ok=True)
    if sys.platform=="win32":
        import ctypes
        try:ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError,OSError):pass
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from niangao.config import Settings
    from niangao.pet import PetWindow
    app=QApplication(sys.argv[:1]);app.setApplicationName("NiangaoPhotoPet");app.setQuitOnLastWindowClosed(False)
    from niangao.art import asset_path
    from PySide6.QtGui import QFontDatabase,QFont
    font_id=QFontDatabase.addApplicationFont(str(asset_path("fonts/NiangaoSans.ttf")))
    if font_id>=0:app.setFont(QFont(QFontDatabase.applicationFontFamilies(font_id)[0],10))
    window=PetWindow(Settings(args.settings),args.probe)
    window.show()
    if args.expanded_smoke:
        def expanded_smoke():
            try:
                from datetime import date
                from niangao.life.calendar_cn import lunar_label
                from niangao.dialogue import _CORPUS
                from niangao.prop_physics import Body
                from niangao.geometry import Rect
                assert len(_CORPUS)==1000 and lunar_label(date(2025,1,29))=="春节"
                normal=window.size();window.set_work_mode(True);assert window.width()==96
                image=window.pixmap.toImage();window.render_frame();assert image==window.pixmap.toImage()
                window.open_work();window.work_panel.text.setText("今天要专注工作");window.work_panel.send()
                assert window.work_panel.isVisible();window.set_work_mode(False);assert window.size()==normal
                window.open_focus();assert window.focus_panel.isVisible()
                body=Body(100,100)
                for _ in range(120):body.advance(1/60,100,100,Rect(0,0,1200,900))
                assert body.grounded and body.y==788
                assert window.perform_action("climb") and window.perform_action("climb_top")
                window.life.data["inventory"]["freeze_dried"]=1
                assert window.desktop.place("freeze_dried")[0]
                uid=next(w.uid for w in window.desktop.widgets.values() if w.id=="freeze_dried")
                assert window.desktop.drop_piece(uid) and window.desktop.widgets[uid].record["remaining"]==7
                window.desktop.clear()
                print("EXPANDED_SMOKE passed: normalized stage, work icon/local chat, focus widget, lunar dates, 1000 lines, gravity, climb assets, single-piece food",flush=True);window.close()
            except Exception:traceback.print_exc();app.exit(1)
        QTimer.singleShot(1200,expanded_smoke)
    if args.desktop_smoke:
        def desktop_smoke():
            try:
                from niangao.life.catalog import BY_ID
                from niangao.life.item_art import item_pixmap
                window.open_life();ui=window.life_window
                assert ui.stack.count()==8 and not any("3D" in ui.nav.item(i).text() for i in range(8))
                assert ui.width()<=900 and window.bubble.width()<244
                assert all(not item_pixmap(id,96).isNull() for id in BY_ID)
                ui.profile_fields["personality"].setPlainText("慢热但亲人");ui.profile_fields["habits"].setPlainText("爱喝清水");ui.save_profile()
                assert ui.client.profile_provider()["identity"]["habits"]=="爱喝清水"
                assert window.desktop.place("water_fountain")[0]
                uid=next(iter(window.desktop.widgets));w=window.desktop.widgets[uid]
                assert window.desktop.activate(uid) and w.record["water"]==80
                window.desktop.refill(uid);assert w.record["water"]==100
                window.desktop.clear();assert not window.desktop.widgets
                print("DESKTOP_SMOKE passed: 8 pages, no 3D space, 50 product images, mandatory profile, fountain drink/refill and cleanup",flush=True);window.close()
            except Exception:traceback.print_exc();app.exit(1)
        QTimer.singleShot(1200,desktop_smoke)
    if args.motion_smoke:
        def motion_smoke():
            try:
                from niangao.interaction.actions import ACTIONS,ROWS,SOUNDS
                from niangao.interaction.audio import synthesize
                checked=0
                for key,info in ACTIONS.items():
                    assert window.perform_action(key),key
                    for i in range(len(window.art.frames[info.resource])):
                        pix,mask=window.art.render(info.resource,i,240,300);assert not mask.isNull();checked+=1
                assert sum(len(v) for v in ROWS.values())==32
                assert all(len(synthesize(k,20))>10000 for k in SOUNDS)
                print("MOTION_SMOKE passed:",len(ACTIONS),"action IDs;",checked,"rendered frames; 9 PCM sound families",flush=True);window.close()
            except Exception:traceback.print_exc();app.exit(1)
        QTimer.singleShot(1200,motion_smoke)
    if args.suite_smoke:
        def suite_smoke():
            try:
                window.open_life();ui=window.life_window
                assert ui.stack.count()==8
                for i in range(8):ui.nav.setCurrentRow(i);app.processEvents()
                ui.care("brush","groom");assert window.behaviour.state=="groom"
                assert window.life.add_task("smoke task")
                ui.generate_diary();assert ui.diary_text.toPlainText()
                ui.grab().save(str((args.probe.parent if args.probe else Path.cwd())/"life-smoke.png"))
                print("LIFE_SMOKE passed: 8 pages, care/action, task, diary",flush=True);window.close()
            except Exception:traceback.print_exc();app.exit(1)
        QTimer.singleShot(1200,suite_smoke)
    elif not args.smoke and not args.probe and not args.motion_smoke and not args.desktop_smoke and not args.expanded_smoke and not window.work_mode:
        QTimer.singleShot(700,window.open_life)
    if args.smoke:
        def smoke():
            try:
                assert not window.mask().isEmpty()
                assert window.windowFlags() & __import__('PySide6.QtCore',fromlist=['Qt']).Qt.WindowType.FramelessWindowHint
                window.feed();window.pet_head();window.toggle_sleep()
                assert window.behaviour.state=="sleep"
                window.toggle_sleep();assert window.behaviour.state=="idle"
                window.resize_pet(260)
                window.grab().save(str((args.probe.parent if args.probe else Path.cwd())/'photo-smoke.png'))
                assert not window.mask().contains(__import__('PySide6.QtCore',fromlist=['QPoint']).QPoint(0,0))
                print("PHOTO_SMOKE passed: alpha region, frameless, interactions, sleep/wake, resize",flush=True)
                window.close()
            except Exception:
                traceback.print_exc();app.exit(1)
        QTimer.singleShot(1200,smoke)
    return app.exec()

if __name__=="__main__":
    try:sys.exit(main())
    except Exception:
        log=Path(os.environ.get("APPDATA",str(Path.home())))/"NiangaoPhotoPet"/"crash.log"
        log.parent.mkdir(parents=True,exist_ok=True);log.write_text(traceback.format_exc(),encoding="utf-8")
        if sys.platform=="win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,"年糕启动失败，错误日志："+str(log),"年糕",0x10)
        raise
