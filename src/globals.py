from PySide6.QtCore import QObject, Signal
from pynput import mouse, keyboard
import concurrent.futures
from qfluentwidgets import DoubleSpinBox
from PySide6.QtWidgets import QApplication
from ok import Logger, og
from threading import Event

logger = Logger.get_logger(__name__)

# --- 猴子补丁 ---
# 修改 DoubleSpinBox，使其默认拥有一个更大的最大值
_original_init = DoubleSpinBox.__init__


def _new_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    self.setMaximum(99999.0)


DoubleSpinBox.__init__ = _new_init


# --- 猴子补丁 ---


class Globals(QObject):
    clicked = Signal(int, int, object, bool)
    pressed = Signal(object)

    def __init__(self, exit_event):
        super().__init__()
        self.pynput_mouse = None
        self.pynput_keyboard = None
        self._thread_pool_executor_max_workers = 0
        self.thread_pool_executor = None
        self.thread_pool_exit_event = Event()
        self.shared_frame = None
        exit_event.bind_stop(self)
        self.init_pynput()

    def stop(self):
        logger.info("pynput stop")
        self.reset_pynput()
        self.shutdown_thread_pool_executor()

    def init_pynput(self):
        logger.info("pynput start")
        if self.pynput_mouse is None:
            self.pynput_mouse = mouse.Listener(on_click=self.on_click)
            self.pynput_mouse.start()
        if self.pynput_keyboard is None:
            self.pynput_keyboard = keyboard.Listener(on_press=self.on_press)
            self.pynput_keyboard.start()

    def reset_pynput(self):
        if self.pynput_mouse:
            self.pynput_mouse.stop()
            self.pynput_mouse = None
        if self.pynput_keyboard:
            self.pynput_keyboard.stop()
            self.pynput_keyboard = None

    def on_click(self, x, y, button, pressed):
        self.clicked.emit(x, y, button, pressed)

    def on_press(self, key):
        self.pressed.emit(key)

    def get_thread_pool_executor(self, max_workers=6):
        """
        获取全局执行器。
        如果请求的 max_workers 大于当前值，将安全地重建线程池。
        """
        if self.thread_pool_executor is not None and max_workers > self._thread_pool_executor_max_workers:
            logger.info(
                f"thread pool max_workers not enough, reset max_workers {self._thread_pool_executor_max_workers} -> {max_workers}")
            self.shutdown_thread_pool_executor()

        if self.thread_pool_executor is None:
            logger.info(f"create thread pool executor, max_workers: {max_workers}")
            self.thread_pool_exit_event.clear() 
            self.thread_pool_executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
            self._thread_pool_executor_max_workers = max_workers

        return self.thread_pool_executor

    def shutdown_thread_pool_executor(self):
        if self.thread_pool_executor is not None:
            logger.info("Shutting down thread pool executor...")
            self.thread_pool_exit_event.set()
            self.thread_pool_executor.shutdown(wait=False, cancel_futures=True)
            self.thread_pool_executor = None
            self._thread_pool_executor_max_workers = 0

    def submit_periodic_task(self, delay, task, *args, **kwargs):
        """
        提交一个循环任务到线程池。
        如果要停止循环，任务函数应返回 False。
        
        :param task: 要执行的函数
        :param delay: 每次执行后的间隔时间（秒）
        :param args: 位置参数
        :param kwargs: 关键字参数
        """
        executor = self.get_thread_pool_executor()

        def loop_wrapper():
            logger.debug(f"Periodic task {task.__name__} started.")
            
            while not self.thread_pool_exit_event.is_set():
                should_stop = False
                try:
                    if task(*args, **kwargs) is False:
                        should_stop = True
                except Exception as e:
                    logger.error(f"Error in periodic task {task.__name__}: {e}")

                if should_stop:
                    logger.debug(f"Periodic task {task.__name__} decided to stop.")
                    break
        
                if self.thread_pool_exit_event.wait(timeout=delay):
                    logger.debug(f"Periodic task {task.__name__} received stop signal.")
                    break
            
            logger.debug(f"Periodic task {task.__name__} stopped.")

        executor.submit(loop_wrapper)

if __name__ == "__main__":
    glbs = Globals(exit_event=None)
