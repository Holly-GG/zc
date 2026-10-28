from PySide6.QtCore import QObject,Signal,Slot,QRunnable,QThreadPool,Qt
class Signals(QObject):
    done=Signal(object)
    failed=Signal(str)
class Job(QRunnable):
    def __init__(self,work):super().__init__();self.work=work;self.signals=Signals()
    def run(self):
        try:self.signals.done.emit(self.work())
        except Exception as exc:self.signals.failed.emit(str(exc)[:300])
JOBS=set()
class Receiver(QObject):
    def __init__(self,job,done,failed):super().__init__();self.job=job;self.done=done;self.failed=failed
    @Slot(object)
    def success(self,value):
        try:self.done(value)
        finally:JOBS.discard(self);self.deleteLater()
    @Slot(str)
    def failure(self,message):
        try:self.failed(message)
        finally:JOBS.discard(self);self.deleteLater()
def run_job(work,done,failed):
    job=Job(work);receiver=Receiver(job,done,failed);JOBS.add(receiver)
    job.signals.done.connect(receiver.success,Qt.ConnectionType.QueuedConnection);job.signals.failed.connect(receiver.failure,Qt.ConnectionType.QueuedConnection)
    QThreadPool.globalInstance().start(job)
