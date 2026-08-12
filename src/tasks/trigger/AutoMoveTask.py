from contextlib import contextmanager
import time

from ok import TriggerTask, Logger, og
from src.scene.DNAScene import DNAScene
from src.tasks.BaseDNATask import BaseDNATask
from src.tasks.BaseListenerTask import BaseListenerTask

from pynput import mouse

logger = Logger.get_logger(__name__)


class TriggerDeactivateException(Exception):
    """停止激活异常。"""
    pass


class AutoMoveTask(BaseListenerTask, BaseDNATask, TriggerTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "自动穿引共鸣"
        self.description = "需主动激活，运行中也可使用左键打断"
        self.scene: DNAScene | None = None
        self.setup_listener_config()
        self.default_config.update({
            '按下时间': 0.50,
            '间隔时间': 0.45,
        })
        self.config_description.update({
            '按下时间': '左键按住多久',
            '间隔时间': '左键释放后等待多久',
        })
        self.manual_activate = False
        self.signal = False
        self.signal_interrupt = False
        self.running = False

    def disable(self):
        """禁用任务时，断开信号连接。"""
        self.reset()
        self.try_disconnect_listener()
        return super().disable()

    def enable(self):
        """启用任务时，信号连接。"""
        self.reset()
        self.try_connect_listener()
        return super().enable()

    def reset(self):
        self.manual_activate = False
        self.signal = False
        self.signal_interrupt = False
        self.running = False

    def run(self):
        if self.signal:
            self.signal = False
            if not self.scene.in_team(self.in_team_and_world):
                return
            if og.device_manager.hwnd_window.is_foreground():
                self.switch_state()

        if self.manual_activate and not self.running:
            self.running = True
            self.submit_periodic_task(0.005, self.do_move)

    @contextmanager
    def left_click_scope(self):
        self.mouse_down()
        try:
            yield
        finally:
            self.mouse_up()

    def do_move(self):
        try:
            with self.left_click_scope():
                self.trig_sleep_check(self.config.get('按下时间', 0.50))
            self.trig_sleep_check(self.config.get("间隔时间", 0.50))
        except TriggerDeactivateException as e:
            logger.info(f"auto_aim_task_deactivate {e}")
            self.running = False
            return False

    def trig_sleep_check(self, sec, check_signal_flag=True):
        if sec <= 0:
            return
        end_time = time.perf_counter() + sec
        step = 0.01
        while True:
            remaining = end_time - time.perf_counter()
            if remaining <= 0:
                break
            s = step if remaining > step else remaining
            time.sleep(s)
            if not self.manual_activate or not self._enabled or self.paused:
                raise TriggerDeactivateException
            if self._should_interrupt(check_signal_flag):
                self.switch_state()

    def _should_interrupt(self, check_signal_flag: bool) -> bool:
        """检查是否应该中断当前操作"""
        return (self.signal_interrupt or
                (check_signal_flag and self.signal) or
                not self.scene.in_team(self.in_team_and_world))

    def switch_state(self):
        self.signal_interrupt = False
        self.signal = False
        self.manual_activate = not self.manual_activate
        if self.manual_activate:
            logger.info("激活快速移动")
        else:
            logger.info("关闭快速移动")

    def on_global_click(self, x, y, button, pressed):
        if self._executor.paused:
            return

        key_map = {
            'x1': mouse.Button.x1,
            'x2': mouse.Button.x2,
            'left': mouse.Button.left,
        }
        interrupt_button = (key_map.get("left"),)
        activate_key_name = self.config.get('激活键', 'x2')

        if activate_key_name == '使用键盘':
            if button not in interrupt_button:
                return

        activate_button = key_map.get(activate_key_name)

        if pressed:
            if button == activate_button:
                self.signal = True
            elif self.manual_activate and button in interrupt_button:
                self.signal_interrupt = True

    def on_global_press(self, key):
        if self._executor.paused or self.config.get('激活键', 'x2') != '使用键盘':
            return
        lower = self.config.get('键盘', 'ctrl_r').lower()
        hot_key = self.normalize_hotkey(lower)
        if self.key_equal(key, hot_key):
            self.signal = True
