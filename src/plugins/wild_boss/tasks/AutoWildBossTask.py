from __future__ import annotations

import threading
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from qfluentwidgets import FluentIcon

from ok import Logger, TaskDisabledException

from src.plugins.wild_boss.data import (
    DEFAULT_BOSS_SCHEDULE,
    get_boss_definition,
)
from src.plugins.wild_boss.dialogs import BossScheduleDialog
from src.plugins.wild_boss.models import (
    BOSS_ACTIVE_DURATION_MINUTES,
    BossScheduleItem,
    BossScheduleSettings,
    HONG_KONG_TIMEZONE,
    find_due_occurrences,
)
from src.plugins.wild_boss.storage import (
    BossRuntimeStorage,
    BossScheduleStorage,
)
from src.tasks.BaseDNATask import BaseDNATask
from src.tasks.DNAOneTimeTask import DNAOneTimeTask


logger = Logger.get_logger(__name__)


class AutoWildBossTask(DNAOneTimeTask, BaseDNATask):
    exclusive_task_group = "automation_schedule"
    CHECK_INTERVAL_SECONDS = 15
    ENTRY_TIME_CHECK_SECONDS = 10
    MOVE_CONFIRM_TIMEOUT_SECONDS = 10
    ENTRY_DIALOG_TIMEOUT_SECONDS = 120
    ENTRY_MONITOR_INTERVAL_SECONDS = 1
    MINIMAP_STABLE_SECONDS = 10
    MINIMAP_CHANGE_THRESHOLD = 1.5
    MINIMAP_CENTER_X = 1492
    MINIMAP_CENTER_Y = 103
    MINIMAP_INNER_RADIUS = 60
    FARM_DURATION_MINUTES = BOSS_ACTIVE_DURATION_MINUTES
    ROOM_LOAD_TIMEOUT_SECONDS = 120
    ROOM_READY_SETTLE_SECONDS = 2.0
    BOSS_READY_DELAY_SECONDS = 10
    BOSS_READY_TIMEOUT_SECONDS = 60
    BOSS_READY_POLL_SECONDS = 1
    BATTLE_TIMEOUT_SECONDS = 120
    EXIT_TIMEOUT_SECONDS = 120

    MAIN_SCREEN_FEATURE = "main_screen_marker_leftdown"
    MENU_FEATURE = "wild_boss_menu"
    ACTIVE_GO_FEATURE = "wild_boss_go_active"
    INACTIVE_GO_FEATURE = "wild_boss_go_inactive"
    MOVE_CONFIRM_FEATURE = "wild_boss_move_confirm"
    ENTRY_CONFIRM_FEATURE = "wild_boss_entry_confirm"
    ENTRY_NOT_READY_FEATURE = "wild_boss_entry_not_ready"
    WAITING_FOR_BOSS_FEATURE = "wild_boss_waiting"
    ROOM_READY_FEATURE = "wild_boss_room_ready"
    VICTORY_FEATURE = "wild_boss_victory"
    SKIP_CUTSCENE_FEATURE = "wild_boss_skip_cutscene"
    EXIT_TASK_FEATURE = "wild_boss_exit_task"
    EXIT_CONFIRM_FEATURE = "wild_boss_exit_confirm"

    BOSS_ROW_Y = (140 / 900, 259 / 900, 378 / 900)
    BOSS_ROW_X = 139 / 1600
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.name = "野外首領排程"
        self.description = (
            "設定排程後按開始；每 15 秒檢查香港時間"
        )
        self.group_name = "全自動"
        self.group_icon = FluentIcon.CALENDAR
        self.icon = FluentIcon.CALENDAR
        self.enable_fidget_action = False

        self.schedule_storage = BossScheduleStorage(
            Path("configs") / "wild_boss_schedule.json"
        )
        self.runtime_storage = BossRuntimeStorage(
            Path("configs") / "wild_boss_runtime.json"
        )
        try:
            self.schedule_settings = self.schedule_storage.load(
                DEFAULT_BOSS_SCHEDULE
            )
        except Exception as error:
            logger.warning(f"Failed to load wild boss schedule: {error}")
            self.schedule_settings = BossScheduleStorage.copy_settings(
                DEFAULT_BOSS_SCHEDULE
            )

        self.completed_occurrences = self.runtime_storage.load_completed()
        self._state_lock = threading.Lock()
        self._pending: tuple[
            str, BossScheduleItem, datetime
        ] | None = None
        self._last_attempt: dict[str, datetime] = {}

        self.config_description.update({
            "編輯野外首領排程": (
                "設定每日 4 個香港時間、啟用狀態及對應首領。"
            ),
        })
        self.config_type.update({
            "編輯野外首領排程": {
                "type": "button",
                "text": "開啟野外首領排程",
                "icon": FluentIcon.CALENDAR,
                "callback": self.open_schedule_dialog,
            },
        })

    def on_create(self) -> None:
        # ConfigCard treats an empty Config as having no expandable content,
        # even when config_type contains a custom button.  Keep one hidden
        # value so the schedule editor row and expand arrow are rendered.
        self.config.setdefault("_schedule_editor_available", True)

    def open_schedule_dialog(self) -> None:
        parent = QApplication.activeWindow()
        dialog = BossScheduleDialog(self.schedule_settings, parent)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        settings = dialog.get_settings()
        try:
            self.schedule_storage.save(settings)
        except Exception as error:
            QMessageBox.critical(parent, "保存失敗", str(error))
            return
        with self._state_lock:
            self.schedule_settings = settings
        self.log_info("野外首領排程已保存（香港時間）")

    def monitor_schedule(self) -> bool:
        now = self.current_hong_kong_time()
        with self._state_lock:
            if self._pending is not None:
                return True
            due = find_due_occurrences(
                self.schedule_settings,
                now,
                self.completed_occurrences,
            )
            if not due:
                return True
            occurrence = due[0]
            key = occurrence[0]
            last_attempt = self._last_attempt.get(key)
            if last_attempt is not None:
                elapsed = (now - last_attempt).total_seconds()
                if elapsed < self.schedule_settings.retry_seconds:
                    return True

            self._pending = occurrence
            self._last_attempt[key] = now

        boss = get_boss_definition(occurrence[1].boss_id)
        self.log_info(
            f"香港時間 {now.strftime('%H:%M:%S')}："
            f"準備前往野外首領 {boss.name}"
        )
        self.execute_occurrence(occurrence)
        return True

    def run(self) -> None:
        DNAOneTimeTask.run(self)
        self.log_info("將遊戲視窗切換到前景並取得鍵盤焦點")
        try:
            self.focus_game_window()
        except Exception as error:
            self.log_info(f"啟動排程時切換遊戲前景失敗：{error}")
        self.log_info(
            "野外首領排程已開始：每 15 秒檢查香港時間，"
            f"到指定時間前 "
            f"{self.schedule_settings.lead_minutes} 分鐘自動執行",
            notify=True,
        )
        while True:
            self.monitor_schedule()
            self.sleep(self.CHECK_INTERVAL_SECONDS)

    def execute_occurrence(
        self,
        pending: tuple[str, BossScheduleItem, datetime],
    ) -> None:
        key, item, scheduled = pending
        boss = get_boss_definition(item.boss_id)
        success = False
        try:
            self.log_info(
                f"執行野外首領：{boss.name}；"
                f"指定時間 {scheduled.strftime('%H:%M')}（香港時間）"
            )
            success = self.execute_boss(
                boss.list_index,
                boss.name,
                scheduled,
            )
            if success:
                self.completed_occurrences.add(key)
                self.runtime_storage.save_completed(
                    self.completed_occurrences
                )
                self.log_info(f"已進入野外首領房：{boss.name}", notify=True)
        except TaskDisabledException:
            raise
        except Exception as error:
            logger.error("Wild boss execution failed", error)
            self.log_info(f"前往野外首領失敗：{error}")
        finally:
            with self._state_lock:
                self._pending = None

        if not success:
            self.log_info("未能前往，會在有效時段內按設定重試")

    def execute_boss(
        self,
        list_index: int,
        boss_name: str,
        scheduled: datetime,
    ) -> bool:
        deadline = scheduled + timedelta(
            minutes=self.FARM_DURATION_MINUTES
        )
        completed_cycles = 0
        while self.current_hong_kong_time() < deadline:
            if not self.navigate_to_boss(list_index, boss_name):
                return False

            entry_state = self.wait_for_entry_dialog()
            if entry_state == "confirm":
                self.log_info(
                    f"已到達 {boss_name}，確認進入首領房"
                )
                self.ensure_in_front()
                self.send_key("space", down_time=0.08, after_sleep=3.0)
                if not self.run_boss_cycle(boss_name, scheduled):
                    return False
                completed_cycles += 1
                now = self.current_hong_kong_time()
                self.log_info(
                    f"{boss_name} 已完成第 {completed_cycles} 輪；"
                    f"目前香港時間 {now.strftime('%H:%M:%S')}"
                )
                continue

            if entry_state == "not_ready":
                self.log_info(
                    f"{boss_name} 尚未到入場時間，關閉提示並等待"
                )
                self.ensure_in_front()
                self.send_key("space", down_time=0.08, after_sleep=1.0)
                self.wait_until_scheduled_time(scheduled, boss_name)
                continue

            if entry_state == "stuck":
                self.recover_from_stuck_entrance(boss_name)
                continue

            self.log_info(
                f"前往 {boss_name} 後等候逾時，"
                "找不到入場確認或未開放提示"
            )
            return False

        self.log_info(
            f"已到 {deadline.strftime('%H:%M:%S')}（香港時間），"
            f"停止重複討伐 {boss_name}；"
            f"完成 {completed_cycles} 輪"
        )
        return completed_cycles > 0

    def navigate_to_boss(self, list_index: int, boss_name: str) -> bool:
        self.log_info("野外首領到期，將遊戲視窗切換到前景")
        self.focus_game_window()
        if not self.ensure_main_screen():
            raise RuntimeError("無法返回遊戲主畫面")

        self.ensure_in_front()
        self.send_key("esc", down_time=0.08, after_sleep=0.8)
        menu_box = self.wait_until(
            lambda: self.find_one(
                self.MENU_FEATURE,
                horizontal_variance=0.03,
                vertical_variance=0.04,
                threshold=0.8,
            ),
            time_out=5,
            raise_if_not_found=False,
        )
        if menu_box is None:
            raise RuntimeError("ESC 選單中找不到野外首領")
        self.move_and_click(menu_box, after_sleep=2.0)

        self.select_boss_row(list_index, boss_name)
        self.log_info(
            f"已選擇 {boss_name}，按第一下 Space 啟動前往"
        )
        self.ensure_in_front()
        self.send_key("space", down_time=0.1, after_sleep=0.8)

        move_confirm = self.wait_until(
            lambda: self.find_one(
                self.MOVE_CONFIRM_FEATURE,
                horizontal_variance=0.04,
                vertical_variance=0.04,
                threshold=0.8,
            ),
            time_out=self.MOVE_CONFIRM_TIMEOUT_SECONDS,
            raise_if_not_found=False,
        )
        if move_confirm is None:
            raise RuntimeError("第一下 Space 後找不到移動確認視窗（30.png）")

        self.log_info(
            f"已辨識移動確認視窗，按第二下 Space 前往 {boss_name}"
        )
        self.ensure_in_front()
        self.send_key("space", down_time=0.1, after_sleep=3.0)
        return True

    def wait_for_entry_dialog(self) -> str | None:
        previous_fingerprint = None
        stable_samples = 0
        sample_limit = int(
            self.ENTRY_DIALOG_TIMEOUT_SECONDS
            / self.ENTRY_MONITOR_INTERVAL_SECONDS
        )

        for _ in range(sample_limit + 1):
            self.next_frame()
            entry_state = self.find_entry_dialog_state()
            if entry_state is not None:
                return entry_state

            if not self.is_main_screen():
                previous_fingerprint = None
                stable_samples = 0
            else:
                fingerprint = self.get_minimap_inner_fingerprint()
                if fingerprint is None:
                    previous_fingerprint = None
                    stable_samples = 0
                elif previous_fingerprint is None:
                    previous_fingerprint = fingerprint
                    stable_samples = 0
                else:
                    difference = float(
                        np.mean(
                            np.abs(
                                fingerprint.astype(np.float32)
                                - previous_fingerprint.astype(np.float32)
                            )
                        )
                    )
                    if difference > self.MINIMAP_CHANGE_THRESHOLD:
                        previous_fingerprint = fingerprint
                        stable_samples = 0
                    else:
                        stable_samples += 1
                        stable_seconds = (
                            stable_samples
                            * self.ENTRY_MONITOR_INTERVAL_SECONDS
                        )
                        if stable_seconds >= self.MINIMAP_STABLE_SECONDS:
                            self.log_info(
                                "10 秒內小地圖內部地形冇變化，"
                                "判定角色卡喺 Boss 房入口"
                            )
                            return "stuck"

            self.sleep(self.ENTRY_MONITOR_INTERVAL_SECONDS)

        return None

    def get_minimap_inner_fingerprint(self, frame=None):
        if frame is None:
            frame = self.frame
        if frame is None or frame.size == 0:
            return None

        frame_height, frame_width = frame.shape[:2]
        scale_x = frame_width / 1600
        scale_y = frame_height / 900
        center_x = int(self.MINIMAP_CENTER_X * scale_x)
        center_y = int(self.MINIMAP_CENTER_Y * scale_y)
        radius = max(
            1,
            int(
                self.MINIMAP_INNER_RADIUS
                * min(scale_x, scale_y)
            ),
        )

        x1 = center_x - radius
        y1 = center_y - radius
        x2 = center_x + radius + 1
        y2 = center_y + radius + 1
        if (
            x1 < 0
            or y1 < 0
            or x2 > frame_width
            or y2 > frame_height
        ):
            return None

        crop = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        yy, xx = np.ogrid[:gray.shape[0], :gray.shape[1]]
        inner_circle = (
            (xx - radius) ** 2 + (yy - radius) ** 2
            <= radius ** 2
        )
        return gray[inner_circle]

    def recover_from_stuck_entrance(self, boss_name: str) -> None:
        self.log_info(
            f"前往 {boss_name} 後卡喺入口；按住 S 兩秒後重新前往"
        )
        self.ensure_in_front()
        self.send_key("s", down_time=2.0, after_sleep=1.0)

    def find_entry_dialog_state(self) -> str | None:
        confirm = self.find_one(
            self.ENTRY_CONFIRM_FEATURE,
            horizontal_variance=0.04,
            vertical_variance=0.04,
            threshold=0.8,
        )
        if confirm is not None:
            return "confirm"

        not_ready = self.find_one(
            self.ENTRY_NOT_READY_FEATURE,
            horizontal_variance=0.04,
            vertical_variance=0.04,
            threshold=0.8,
        )
        if not_ready is not None:
            return "not_ready"
        return None

    def wait_until_scheduled_time(
        self,
        scheduled: datetime,
        boss_name: str,
    ) -> None:
        while True:
            now = self.current_hong_kong_time()
            remaining = (scheduled - now).total_seconds()
            if remaining <= 0:
                self.log_info(
                    f"已到 {scheduled.strftime('%H:%M:%S')}（香港時間），"
                    f"重新前往 {boss_name}"
                )
                return

            self.log_info(
                f"目前香港時間 {now.strftime('%H:%M:%S')}；"
                f"距離 {boss_name} 入場時間尚餘 "
                f"{int(remaining + 0.999)} 秒"
            )
            self.sleep(
                min(self.ENTRY_TIME_CHECK_SECONDS, remaining)
            )

    @staticmethod
    def current_hong_kong_time() -> datetime:
        return datetime.now(HONG_KONG_TIMEZONE)

    def run_boss_cycle(
        self,
        boss_name: str,
        scheduled: datetime,
    ) -> bool:
        room_main_screen = self.wait_until(
            self.is_main_screen,
            time_out=self.ROOM_LOAD_TIMEOUT_SECONDS,
            raise_if_not_found=False,
        )
        if not room_main_screen:
            self.log_info(
                f"進入 {boss_name} 房後找不到主畫面"
            )
            return False

        if not self.wait_until_boss_ready(scheduled, boss_name):
            return False

        self.log_info(
            f"{boss_name} 房已載入，等待畫面穩定後按 Space 開始自動戰鬥"
        )
        self.sleep(self.ROOM_READY_SETTLE_SECONDS)
        self.ensure_in_front()
        self.send_key("space", down_time=0.3, after_sleep=1.5)

        battle_complete = self.wait_for_battle_completion()
        if battle_complete is None:
            self.log_info(
                f"等待 {boss_name} 戰鬥完成 2 分鐘逾時；"
                "未見右側任務欄『的領域』標記"
            )
            return False

        self.log_info(
            f"已辨識 {boss_name} 房內『的領域』標記，"
            "點擊任務文字開啟離開提示"
        )
        self.move_and_click(battle_complete, after_sleep=1.5)

        exit_confirm = self.wait_for_feature(
            self.EXIT_CONFIRM_FEATURE,
            self.EXIT_TIMEOUT_SECONDS,
        )
        if exit_confirm is None:
            self.log_info(
                f"找不到離開 {boss_name} 房嘅確認提示"
            )
            return False

        self.log_info(f"確認離開 {boss_name} 房")
        self.ensure_in_front()
        self.send_key("space", down_time=0.08, after_sleep=3.0)

        outside = self.wait_until(
            self.is_outside_boss_room,
            time_out=self.EXIT_TIMEOUT_SECONDS,
            raise_if_not_found=False,
        )
        if not outside:
            self.log_info(
                f"離開 {boss_name} 房後未能確認返回普通主畫面"
            )
            return False
        return True

    def wait_until_boss_ready(
        self,
        scheduled: datetime,
        boss_name: str,
    ) -> bool:
        ready_not_before = scheduled + timedelta(
            seconds=self.BOSS_READY_DELAY_SECONDS
        )
        now = self.current_hong_kong_time()
        if now < ready_not_before:
            self.log_info(
                f"已進入 {boss_name} 房；等待至 "
                f"{ready_not_before.strftime('%H:%M:%S')}（香港時間）"
                "先檢查 Boss 是否出現"
            )

        while now < ready_not_before:
            self.sleep(
                min(
                    self.BOSS_READY_POLL_SECONDS,
                    (ready_not_before - now).total_seconds(),
                )
            )
            now = self.current_hong_kong_time()

        readiness_deadline = max(
            scheduled + timedelta(
                seconds=self.BOSS_READY_TIMEOUT_SECONDS
            ),
            now + timedelta(seconds=10),
        )
        self.log_info(
            f"已到 {ready_not_before.strftime('%H:%M:%S')}（香港時間）；"
            f"等待 {boss_name} 動畫完結、31.png 消失及"
            "右側任務欄『討伐』標記出現"
        )

        while now < readiness_deadline:
            if self.is_boss_ready_to_fight():
                self.log_info(
                    f"{boss_name} 已出現：主畫面正常、"
                    "31.png 已消失、右側任務欄『討伐』標記已出現"
                )
                return True
            self.sleep(self.BOSS_READY_POLL_SECONDS)
            now = self.current_hong_kong_time()

        self.log_info(
            f"等待 {boss_name} 出現逾時；未能同時確認主畫面、"
            "31.png 消失及右側任務欄『討伐』標記出現"
        )
        return False

    def is_boss_ready_to_fight(self) -> bool:
        if not self.is_main_screen():
            return False

        waiting = self.find_one(
            self.WAITING_FOR_BOSS_FEATURE,
            horizontal_variance=0.04,
            vertical_variance=0.04,
            threshold=0.8,
        )
        if waiting is not None:
            return False

        return self.find_one(
            self.ROOM_READY_FEATURE,
            horizontal_variance=0.04,
            vertical_variance=0.04,
            threshold=0.82,
        ) is not None

    def wait_for_battle_completion(self):
        self._battle_victory_confirmed = False
        return self.wait_until(
            self.find_battle_completion_or_handle_overlay,
            time_out=self.BATTLE_TIMEOUT_SECONDS,
            raise_if_not_found=False,
        )

    def find_battle_completion_or_handle_overlay(self):
        victory = self.find_one(
            self.VICTORY_FEATURE,
            horizontal_variance=0.04,
            vertical_variance=0.04,
            threshold=0.82,
        )
        if victory is not None:
            self.log_info("偵測到 17.png 勝利確認，按 Space 繼續")
            self.ensure_in_front()
            self.send_key("space", down_time=0.08, after_sleep=1.0)
            self._battle_victory_confirmed = True
            return None

        skip_cutscene = self.find_one(
            self.SKIP_CUTSCENE_FEATURE,
            horizontal_variance=0.02,
            vertical_variance=0.02,
            threshold=0.82,
        )
        if skip_cutscene is not None:
            self.log_info("偵測到過場動畫，點擊右上角『跳過動畫』")
            self.move_and_click(skip_cutscene, after_sleep=0.1)
            self.pydirect_interaction.move(
                int(self.width * 0.5),
                int(self.height * 0.5),
            )
            self.sleep(0.9)
            return None

        exit_task = self.find_one(
            self.EXIT_TASK_FEATURE,
            horizontal_variance=0.04,
            vertical_variance=0.04,
            threshold=0.82,
        )
        if exit_task is None:
            return None
        if not getattr(self, "_battle_victory_confirmed", False):
            self.log_info(
                "右側任務欄『的領域』已出現，但仍未見 17.png；繼續等候"
            )
            return None
        return exit_task

    def wait_for_feature(self, feature_name: str, timeout: float):
        return self.wait_until(
            lambda: self.find_one(
                feature_name,
                horizontal_variance=0.04,
                vertical_variance=0.04,
                threshold=0.82,
            ),
            time_out=timeout,
            raise_if_not_found=False,
        )

    def is_outside_boss_room(self) -> bool:
        if not self.is_main_screen():
            return False
        room_task = self.find_one(
            self.ROOM_READY_FEATURE,
            horizontal_variance=0.04,
            vertical_variance=0.04,
            threshold=0.82,
        )
        return room_task is None

    def ensure_main_screen(self) -> bool:
        if self.is_main_screen():
            return True
        for attempt in range(1, 6):
            self.ensure_in_front()
            self.send_key("esc", down_time=0.08, after_sleep=0.8)
            if self.wait_until(
                self.is_main_screen,
                time_out=2,
                raise_if_not_found=False,
            ):
                self.log_info(f"按 ESC {attempt} 次後返回主畫面")
                return True
        return False

    def is_main_screen(self) -> bool:
        return self.find_one(
            self.MAIN_SCREEN_FEATURE,
            horizontal_variance=0.01,
            vertical_variance=0.01,
            threshold=0.8,
        ) is not None

    def select_boss_row(self, list_index: int, boss_name: str) -> None:
        visible_index = list_index
        if list_index >= len(self.BOSS_ROW_Y):
            scroll_count = list_index - len(self.BOSS_ROW_Y) + 1
            for _ in range(scroll_count):
                self.pydirect_interaction.scroll(
                    int(self.width * self.BOSS_ROW_X),
                    int(self.height * self.BOSS_ROW_Y[-1]),
                    -5,
                )
                self.sleep(0.5)
            visible_index = len(self.BOSS_ROW_Y) - 1

        x = int(self.width * self.BOSS_ROW_X)
        y = int(self.height * self.BOSS_ROW_Y[visible_index])
        self.log_info(f"選擇野外首領 {boss_name}：({x}, {y})")
        self.ensure_in_front()
        self.pydirect_interaction.move(x, y)
        self.sleep(0.2)
        self.pydirect_interaction.click(down_time=0.1)
        self.sleep(1.5)

    def move_and_click(self, box, after_sleep: float = 1.0) -> None:
        x = int(box.x + box.width / 2)
        y = int(box.y + box.height / 2)
        self.log_info(
            f"點擊 {box.name} 中心：({x}, {y})"
        )
        self.ensure_in_front()
        self.pydirect_interaction.move(x, y)
        self.sleep(0.2)
        self.pydirect_interaction.click(down_time=0.1)
        self.sleep(after_sleep)
