from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Iterable, Mapping, Sequence

import cv2
import numpy as np
from ok import Box, Logger
from qfluentwidgets import FluentIcon

from src.tasks.BaseDNATask import BaseDNATask
from src.tasks.DNAOneTimeTask import DNAOneTimeTask


logger = Logger.get_logger(__name__)


@dataclass(frozen=True)
class MapEventDefinition:
    event_id: str
    config_key: str
    display_name: str
    row_feature: str
    zero_feature: str
    one_feature: str
    event_kind: str


OMINOUS_EVENT = MapEventDefinition(
    event_id="ominous_barrier",
    config_key="不祥的召喚結界",
    display_name="不祥的召喚結界",
    row_feature="46_01",
    zero_feature="49_01",
    one_feature="51_01",
    event_kind="ominous",
)
DEEP_HOLE_EVENT = MapEventDefinition(
    event_id="deep_hole",
    config_key="通往深層的黑色坑洞",
    display_name="通往深層的黑色坑洞",
    row_feature="46_02",
    zero_feature="48_01",
    one_feature="44_01",
    event_kind="black_hole",
)
UNDERGROUND_HOLE_EVENT = MapEventDefinition(
    event_id="underground_hole",
    config_key="通往地下的黑色坑洞",
    display_name="通往地下的黑色坑洞",
    row_feature="46_03",
    zero_feature="48_01",
    one_feature="44_01",
    event_kind="black_hole",
)

# This tuple is also the required selection priority.
EVENT_PRIORITY: tuple[MapEventDefinition, ...] = (
    OMINOUS_EVENT,
    DEEP_HOLE_EVENT,
    UNDERGROUND_HOLE_EVENT,
)

TARGET_REGION_CONFIG_KEY = "指定狩獵場地區"
TARGET_REGION_FEATURES = {
    "冰霜狹谷": "56_01",
}
TARGET_REGION_LOCAL_FEATURES = {
    "冰霜狹谷": "56_02",
}


def selected_events_from_config(
    config: Mapping[str, object] | None,
) -> tuple[MapEventDefinition, ...]:
    """Return selected events in the fixed gameplay priority order."""
    values = config or {}
    return tuple(
        event for event in EVENT_PRIORITY if bool(values.get(event.config_key, False))
    )


def event_row_color_fraction(frame: np.ndarray, row: Box) -> float:
    """Measure the coloured icon immediately to the left of an event row."""
    if frame is None or frame.size == 0 or row.height <= 0:
        return 0.0

    scale = row.height / 16.0
    height, width = frame.shape[:2]
    x1 = max(0, row.x - round(62 * scale))
    x2 = min(width, row.x - round(4 * scale))
    y1 = max(0, row.y - round(25 * scale))
    y2 = min(height, row.y + round(35 * scale))
    if x2 <= x1 or y2 <= y1:
        return 0.0

    icon = frame[y1:y2, x1:x2, :3]
    hsv = cv2.cvtColor(icon, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    coloured = (saturation > 80) & (value > 55)
    return float(np.count_nonzero(coloured) / coloured.size)


def event_row_is_available(frame: np.ndarray, row: Box) -> bool:
    """Return False for a grey, semi-transparent event-list row."""
    return event_row_color_fraction(frame, row) >= 0.35


def choose_available_event(
    selected: Sequence[MapEventDefinition],
    rows_by_event: Mapping[str, Sequence[Box]],
    frame: np.ndarray,
) -> tuple[MapEventDefinition, Box] | None:
    """Choose the first coloured row according to EVENT_PRIORITY."""
    selected_ids = {event.event_id for event in selected}
    for event in EVENT_PRIORITY:
        if event.event_id not in selected_ids:
            continue
        coloured_rows = [
            row
            for row in rows_by_event.get(event.event_id, ())
            if event_row_is_available(frame, row)
        ]
        if coloured_rows:
            best = max(
                coloured_rows,
                key=lambda row: (event_row_color_fraction(frame, row), row.confidence),
            )
            return event, best
    return None


def event_detail_panel_is_visible(frame: np.ndarray) -> bool:
    """Detect the large purple 'go here' button in the event detail panel."""
    if frame is None or frame.size == 0:
        return False
    height, width = frame.shape[:2]
    button = frame[
        round(height * 0.87) : round(height * 0.97),
        round(width * 0.55) : round(width * 0.96),
        :3,
    ]
    if button.size == 0:
        return False
    hsv = cv2.cvtColor(button, cv2.COLOR_BGR2HSV)
    purple = (
        (hsv[:, :, 0] >= 120)
        & (hsv[:, :, 0] <= 155)
        & (hsv[:, :, 1] >= 80)
        & (hsv[:, :, 2] >= 100)
    )
    return float(np.count_nonzero(purple) / purple.size) >= 0.5


def seconds_until_next_minute_five(now: datetime) -> float:
    """Return the wait until the next HH:05 boundary."""
    target = now.replace(minute=5, second=0, microsecond=0)
    if target <= now:
        target += timedelta(hours=1)
    return max(0.0, (target - now).total_seconds())


class AutoMapEventTask(DNAOneTimeTask, BaseDNATask):
    if TYPE_CHECKING:
        config: Any
        find_feature: Any
        find_one: Any
        send_key: Any

    exclusive_task_group = "automation_schedule"

    MAP_ROW_SEARCH = (0.03, 0.58, 0.13, 0.29)
    MAP_CONFIRM_THRESHOLD = 0.80
    ROW_MATCH_THRESHOLD = 0.90
    STATE_MATCH_THRESHOLD = 0.85
    MAP_OPEN_TIMEOUT_SECONDS = 10
    DETAIL_OPEN_TIMEOUT_SECONDS = 6
    MAP_RESCAN_SECONDS = 5
    STARTUP_FOREGROUND_SETTLE_SECONDS = 1.0
    FOREGROUND_SETTLE_SECONDS = 2.0
    CLICK_RETURN_DELAY_SECONDS = 1.0
    WORLD_MAP_OPEN_DELAY_SECONDS = 1.5
    WORLD_MAP_ENTRY_FEATURE = "55_01"
    WORLD_MAP_ENTRY_THRESHOLD = 0.85
    TARGET_REGION_THRESHOLD = 0.85
    TARGET_REGION_LOCAL_THRESHOLD = 0.85
    WORLD_MAP_CONTROL_SEARCH = (0.02, 0.01, 0.20, 0.10)
    WORLD_MAP_REGION_SEARCH = (0.04, 0.10, 0.80, 0.70)
    TARGET_REGION_LOCAL_SEARCH = (0.03, 0.86, 0.15, 0.12)
    WORLD_MAP_DRAG_DURATION_SECONDS = 0.3
    WORLD_MAP_DRAG_SETTLE_SECONDS = 0.4
    WORLD_MAP_DRAG_STEPS = 6
    WORLD_MAP_DRAG_DIRECTIONS = (
        (0.82, 0.45, 0.18, 0.45),
        (0.50, 0.22, 0.50, 0.70),
        (0.50, 0.70, 0.50, 0.22),
        (0.18, 0.45, 0.82, 0.45),
        (0.50, 0.22, 0.50, 0.70),
        (0.50, 0.70, 0.50, 0.22),
    )
    TRAVEL_TIMEOUT_SECONDS = 300
    ROOM_LOAD_TIMEOUT_SECONDS = 120
    BATTLE_TIMEOUT_SECONDS = 900
    BLACK_HOLE_POST_BATTLE_SECONDS = 20
    WAIT_LOG_INTERVAL_SECONDS = 30

    MAP_CONFIRM_FEATURES = ("46_01", "46_02", "46_03", "46_04")
    MAIN_SCREEN_FEATURE = "main_screen_marker_leftdown"
    BLACK_HOLE_ENTRY_FEATURE = "41_01"
    BLACK_HOLE_ROOM_READY_FEATURE = "42_01"
    BLACK_HOLE_COMPLETE_FEATURE = "40_01"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.name = "自動狩獵場事件"
        self.description = "按優先次序自動完成已選擇的地圖事件"
        self.group_name = "全自動"
        self.group_icon = FluentIcon.GLOBE
        self.icon = FluentIcon.GLOBE
        self.enable_fidget_action = False
        self.enable_bottom_confirm_check()

        self.default_config.update(
            {
                TARGET_REGION_CONFIG_KEY: "冰霜狹谷",
                OMINOUS_EVENT.config_key: False,
                DEEP_HOLE_EVENT.config_key: False,
                UNDERGROUND_HOLE_EVENT.config_key: False,
            }
        )
        self.config_description.update(
            {
                TARGET_REGION_CONFIG_KEY: "每次開地圖後先前往此狩獵場地區。",
                OMINOUS_EVENT.config_key: "整點活動；同時出現時優先處理。",
                DEEP_HOLE_EVENT.config_key: "優先度高於通往地下的黑色坑洞。",
                UNDERGROUND_HOLE_EVENT.config_key: "三種事件中的第三優先。",
            }
        )
        self.config_type.update(
            {
                TARGET_REGION_CONFIG_KEY: {
                    "type": "drop_down",
                    "options": list(TARGET_REGION_FEATURES),
                }
            }
        )

    def run(self) -> None:
        DNAOneTimeTask.run(self)
        self.focus_game_window()
        self.sleep(self.STARTUP_FOREGROUND_SETTLE_SECONDS)
        selected = selected_events_from_config(self.config)
        if not selected:
            self.log_info("未選擇任何地圖事件，任務結束", notify=True)
            return

        self.log_info(
            "已選擇地圖事件："
            + "、".join(event.display_name for event in selected),
            notify=True,
        )
        initially_checked: set[str] = set()
        completed: set[str] = set()
        if not self.ensure_main_screen():
            raise RuntimeError("無法返回遊戲主畫面")
        self.open_map()
        last_wait_log = float("-inf")

        while not self._all_completed(selected, completed):
            remaining = tuple(
                event for event in selected if event.event_id not in completed
            )
            choice = self.find_available_event(remaining)
            if choice is None:
                now = time.monotonic()
                if now - last_wait_log >= self.WAIT_LOG_INTERVAL_SECONDS:
                    self.log_info("暫時未有已選擇且可進入的地圖事件，繼續等候")
                    last_wait_log = now
                self.sleep(self.MAP_RESCAN_SECONDS)
                continue

            event, row = choice
            self.prepare_foreground_after_event_detection()
            self.log_info(f"按優先次序選擇：{event.display_name}")
            self.click_event_row(row)
            if not self.wait_for_event_detail_panel():
                self.log_info(f"{event.display_name} 詳情視窗未載入，返回地圖重試")
                self.send_key("esc", after_sleep=1.0)
                continue

            first_check = event.event_id not in initially_checked
            count_state = self.detect_count_state(event, check_zero=first_check)
            initially_checked.add(event.event_id)

            if count_state == "zero":
                completed.add(event.event_id)
                self.log_info(f"{event.display_name} 首次檢查為 0 次，標記完成")
                self.send_key("esc", after_sleep=1.0)
                continue

            final_run = count_state == "one"
            if final_run:
                self.log_info(f"{event.display_name} 剩餘 1 次，今次為最後一次")
            else:
                self.log_info(f"{event.display_name} 尚多於 1 次，完成後再檢查")

            self.send_key("space", down_time=0.08, after_sleep=2.0)
            if event.event_kind == "ominous":
                self.wait_for_ominous_event_end()
            else:
                self.complete_black_hole_event(event)

            if final_run:
                completed.add(event.event_id)
                self.log_info(f"{event.display_name} 最後一次已完成")

            if self._all_completed(selected, completed):
                break
            self.open_map()

        self.log_info("所有已選擇地圖事件都已完成", notify=True)

    @staticmethod
    def _all_completed(
        selected: Iterable[MapEventDefinition], completed: set[str]
    ) -> bool:
        return all(event.event_id in completed for event in selected)

    def open_map(self) -> None:
        self.log_info("按 M 打開地圖")
        self.send_key("m", down_time=0.08, after_sleep=1.0)

        target_region = str(
            self.config.get(TARGET_REGION_CONFIG_KEY, "冰霜狹谷")
        )
        target_feature = TARGET_REGION_FEATURES.get(target_region)
        target_local_feature = TARGET_REGION_LOCAL_FEATURES.get(target_region)
        if target_feature is None or target_local_feature is None:
            raise RuntimeError(f"未支援的狩獵場地區：{target_region}")

        if self.find_current_target_region(target_local_feature) is not None:
            self.log_info(
                f"辨識到 {target_local_feature}，目前已在 {target_region}，"
                "直接搜尋左下角事件"
            )
            self.wait_for_map_event_list()
            return

        world_map_entry = self.wait_for_feature_in_box(
            self.WORLD_MAP_ENTRY_FEATURE,
            self._world_map_control_search_box(),
            self.WORLD_MAP_ENTRY_THRESHOLD,
            self.MAP_OPEN_TIMEOUT_SECONDS,
        )
        if world_map_entry is None:
            raise RuntimeError("按 M 後未能辨識大地圖入口 55_01")

        self.log_info("辨識到 55_01，點擊進入大地圖")
        self.click_map_box(
            world_map_entry,
            click_at_top=False,
            total_after_click=self.WORLD_MAP_OPEN_DELAY_SECONDS,
        )

        region_match = self.find_target_region_with_drag(target_feature)
        if region_match is None:
            raise RuntimeError(f"拖動大地圖後仍未能找到：{target_region}")

        self.log_info(
            f"辨識到指定狩獵場地區：{target_region}，點擊地區名稱上方"
        )
        self.click_map_box(region_match, click_at_top=True)

        self.wait_for_map_event_list()

    def _target_region_local_search_box(self) -> Box:
        x, y, width, height = self.TARGET_REGION_LOCAL_SEARCH
        return self.box_of_screen(x, y, width=width, height=height)

    def find_current_target_region(self, feature_name: str) -> Box | None:
        return self.find_one(
            feature_name,
            box=self._target_region_local_search_box(),
            threshold=self.TARGET_REGION_LOCAL_THRESHOLD,
        )

    def wait_for_map_event_list(self) -> None:
        deadline = time.monotonic() + self.MAP_OPEN_TIMEOUT_SECONDS
        last_scores: dict[str, float] = {}
        while time.monotonic() < deadline:
            match, last_scores = self.find_map_confirmation()
            if match is not None:
                return
            self.sleep(0.5)
        score_text = ", ".join(
            f"{name}={score:.3f}" for name, score in last_scores.items()
        )
        self.log_info(f"地圖確認模板分數：{score_text or '沒有結果'}")
        raise RuntimeError("按 M 後未能確認地圖事件清單")

    def _world_map_control_search_box(self) -> Box:
        x, y, width, height = self.WORLD_MAP_CONTROL_SEARCH
        return self.box_of_screen(x, y, width=width, height=height)

    def _world_map_region_search_box(self) -> Box:
        x, y, width, height = self.WORLD_MAP_REGION_SEARCH
        return self.box_of_screen(x, y, width=width, height=height)

    def wait_for_feature_in_box(
        self,
        feature_name: str,
        search_box: Box,
        threshold: float,
        timeout: float,
    ) -> Box | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            match = self.find_one(
                feature_name,
                box=search_box,
                threshold=threshold,
            )
            if match is not None:
                return match
            self.sleep(0.25)
        return None

    def find_target_region_with_drag(self, feature_name: str) -> Box | None:
        search_box = self._world_map_region_search_box()
        match = self.find_one(
            feature_name,
            box=search_box,
            threshold=self.TARGET_REGION_THRESHOLD,
        )
        if match is not None:
            return match

        self.log_info("目前大地圖未見指定地區，開始拖動地圖搜尋")
        for index, direction in enumerate(self.WORLD_MAP_DRAG_DIRECTIONS, start=1):
            from_x, from_y, to_x, to_y = direction
            self.log_info(
                f"拖動大地圖第 {index} 次："
                f"({from_x:.2f}, {from_y:.2f}) → ({to_x:.2f}, {to_y:.2f})"
            )
            self.drag_world_map(
                from_x,
                from_y,
                to_x,
                to_y,
            )
            match = self.find_one(
                feature_name,
                box=search_box,
                threshold=self.TARGET_REGION_THRESHOLD,
            )
            if match is not None:
                self.log_info(f"拖動大地圖 {index} 次後找到指定地區")
                return match
        return None

    def drag_world_map(
        self,
        from_x: float,
        from_y: float,
        to_x: float,
        to_y: float,
    ) -> None:
        """Perform a visible real-mouse drag over the world map."""
        start_x = int(self.width * from_x)
        start_y = int(self.height * from_y)
        end_x = int(self.width * to_x)
        end_y = int(self.height * to_y)
        steps = max(1, int(self.WORLD_MAP_DRAG_STEPS))
        step_delay = self.WORLD_MAP_DRAG_DURATION_SECONDS / steps

        self.ensure_in_front()
        self.pydirect_interaction.move(start_x, start_y)
        self.sleep(0.1)
        self.check_bottom_confirm_before_action()
        self.pydirect_interaction.mouse_down(key="left")
        try:
            for step in range(1, steps + 1):
                progress = step / steps
                x = round(start_x + (end_x - start_x) * progress)
                y = round(start_y + (end_y - start_y) * progress)
                self.pydirect_interaction.move(x, y)
                self.sleep(step_delay)
        finally:
            self.pydirect_interaction.mouse_up(key="left")
        self.sleep(self.WORLD_MAP_DRAG_SETTLE_SECONDS)

    def click_map_box(
        self,
        box: Box,
        *,
        click_at_top: bool,
        total_after_click: float | None = None,
    ) -> None:
        x = int(box.x + box.width / 2)
        y = int(box.y if click_at_top else box.y + box.height / 2)
        self.log_info(f"實際點擊 {box.name}：({x}, {y})")
        self.ensure_in_front()
        self.pydirect_interaction.move(x, y)
        self.sleep(0.2)
        self.check_bottom_confirm_before_action()
        self.pydirect_interaction.click(down_time=0.1)
        self.sleep(self.CLICK_RETURN_DELAY_SECONDS)
        self.pydirect_interaction.move(self.width // 2, self.height // 2)
        requested_delay = (
            self.CLICK_RETURN_DELAY_SECONDS
            if total_after_click is None
            else total_after_click
        )
        remaining_delay = requested_delay - self.CLICK_RETURN_DELAY_SECONDS
        if remaining_delay > 0:
            self.sleep(remaining_delay)

    def _map_row_search_box(self) -> Box:
        x, y, width, height = self.MAP_ROW_SEARCH
        return self.box_of_screen(x, y, width=width, height=height)

    def find_map_confirmation(self) -> tuple[Box | None, dict[str, float]]:
        """Confirm the map with any event row, including grey rows."""
        frame = self.frame
        search_box = self._map_row_search_box()
        scores: dict[str, float] = {}
        best_match: Box | None = None
        for feature_name in self.MAP_CONFIRM_FEATURES:
            match = self.find_one(
                feature_name,
                box=search_box,
                threshold=-1.0,
                frame=frame,
                limit=1,
            )
            if match is None:
                continue
            scores[feature_name] = float(match.confidence)
            if best_match is None or match.confidence > best_match.confidence:
                best_match = match
        if (
            best_match is not None
            and best_match.confidence >= self.MAP_CONFIRM_THRESHOLD
        ):
            return best_match, scores
        return None, scores

    def find_available_event(
        self, selected: Sequence[MapEventDefinition]
    ) -> tuple[MapEventDefinition, Box] | None:
        frame = self.frame
        search_box = self._map_row_search_box()
        rows_by_event: dict[str, list[Box]] = {}
        for event in selected:
            rows_by_event[event.event_id] = list(
                self.find_feature(
                    event.row_feature,
                    box=search_box,
                    threshold=self.ROW_MATCH_THRESHOLD,
                    frame=frame,
                    limit=8,
                )
            )
        return choose_available_event(selected, rows_by_event, frame)

    def prepare_foreground_after_event_detection(self) -> None:
        self.log_info(
            "辨識到可進入的地圖事件，將遊戲視窗拉到前景並等待 2 秒"
        )
        self.focus_game_window()
        self.sleep(self.FOREGROUND_SETTLE_SECONDS)

    def click_event_row(self, row: Box) -> None:
        """Click a Unity map row with real mouse input, not PostMessage."""
        x = int(row.x + row.width / 2)
        y = int(row.y + row.height / 2)
        self.log_info(f"實際點擊 {row.name}：({x}, {y})")
        self.ensure_in_front()
        self.pydirect_interaction.move(x, y)
        self.sleep(0.2)
        self.check_bottom_confirm_before_action()
        self.pydirect_interaction.click(down_time=0.1)
        self.sleep(1.0)
        self.pydirect_interaction.move(self.width // 2, self.height // 2)

    def is_main_screen(self) -> bool:
        return self.find_one(
            self.MAIN_SCREEN_FEATURE,
            horizontal_variance=0.01,
            vertical_variance=0.01,
            threshold=0.8,
        ) is not None

    def ensure_main_screen(self) -> bool:
        """Match the Wild Boss startup recovery before opening the map."""
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

    def wait_for_event_detail_panel(self) -> bool:
        deadline = time.monotonic() + self.DETAIL_OPEN_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if event_detail_panel_is_visible(self.frame):
                self.sleep(0.5)
                return True
            self.sleep(0.25)
        return False

    def detect_count_state(
        self, event: MapEventDefinition, *, check_zero: bool
    ) -> str:
        for _ in range(3):
            if check_zero and self.find_one(
                event.zero_feature,
                threshold=self.STATE_MATCH_THRESHOLD,
            ) is not None:
                return "zero"
            if self.find_one(
                event.one_feature,
                threshold=self.STATE_MATCH_THRESHOLD,
            ) is not None:
                return "one"
            self.sleep(0.3)
        return "many"

    def wait_for_ominous_event_end(self) -> None:
        wait_seconds = seconds_until_next_minute_five(datetime.now())
        self.log_info(
            f"不祥的召喚結界自動戰鬥中，等待約 {int(wait_seconds)} 秒至 05 分"
        )
        self.sleep(wait_seconds + 2.0)

    def complete_black_hole_event(self, event: MapEventDefinition) -> None:
        self.log_info(f"等待自動前往 {event.display_name}")
        self.wait_for_stage(
            self.BLACK_HOLE_ENTRY_FEATURE,
            self.TRAVEL_TIMEOUT_SECONDS,
            "到達黑色坑洞後未見跳入確認",
        )
        self.log_info("辨識到跳入確認，按 Space 進入")
        self.send_key("space", down_time=0.08, after_sleep=2.0)

        self.wait_for_stage(
            self.BLACK_HOLE_ROOM_READY_FEATURE,
            self.ROOM_LOAD_TIMEOUT_SECONDS,
            "進入黑色坑洞後未見開始戰鬥提示",
        )
        self.log_info("辨識到房內開始提示，按 Space 開始自動戰鬥")
        self.send_key("space", down_time=0.08, after_sleep=2.0)

        self.wait_for_stage(
            self.BLACK_HOLE_COMPLETE_FEATURE,
            self.BATTLE_TIMEOUT_SECONDS,
            "等待黑色坑洞完成逾時",
        )
        self.log_info("辨識到黑色坑洞完成，等待 20 秒")
        self.sleep(self.BLACK_HOLE_POST_BATTLE_SECONDS)

    def wait_for_stage(
        self, feature_name: str, timeout: float, timeout_message: str
    ) -> Box:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            match = self.find_one(
                feature_name,
                threshold=self.STATE_MATCH_THRESHOLD,
            )
            if match is not None:
                return match
            self.sleep(1.0)
        raise RuntimeError(timeout_message)
