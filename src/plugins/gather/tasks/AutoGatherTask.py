import time
from pathlib import Path

import win32api  # type: ignore[import-untyped]
import win32con  # type: ignore[import-untyped]
import win32gui  # type: ignore[import-untyped]

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
)
from qfluentwidgets import FluentIcon

from ok import Box, Logger, TaskDisabledException

from src.plugins.gather.data.gather_database import (
    get_resource_definition,
    get_skill_definition,
    validate_gather_database,
)
from src.plugins.gather.data.gather_defaults import (
    DEFAULT_GATHER_SETTINGS,
)
from src.plugins.gather.dialogs import (
    GatherQueueDialog,
)
from src.plugins.gather.managers import (
    GatherQueueManager,
)
from src.plugins.gather.models import (
    GatherItem,
    GatherQueueSettings,
)
from src.plugins.gather.pages import (
    CharacterPage,
    GatherPage,
    LifeSkillPage,
    MainScreenPage,
)
from src.plugins.gather.storage import (
    GatherQueueStorage,
)

from src.tasks.BaseDNATask import BaseDNATask
from src.tasks.DNAOneTimeTask import DNAOneTimeTask


logger = Logger.get_logger(__name__)


class AutoGatherTask(
    DNAOneTimeTask,
    BaseDNATask,
):
    exclusive_task_group = "automation_schedule"

    """
    自動採集排程。

    流程：
    1. 從目前 Task GUI 設定讀取排程
    2. 將 GUI 設定轉換成 GatherQueueManager
    3. 按排程順序執行採集
    4. 每個採集項目在指定時間內重複執行
    5. 如開啟循環，全部排程完成後由第一項重新開始
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.enable_fidget_action = False

        # Page Object
        self.character_page = CharacterPage(self)
        self.life_skill_page = LifeSkillPage(self)
        self.gather_page = GatherPage(self)
        # 主畫面偵測
        self.main_screen_page = MainScreenPage(self)

        self.gather_queue_storage = GatherQueueStorage(
            file_path=Path(
                "configs"
            ) / "gather_queue.json"
        )

        # Dialog 使用的目前排程。
        # GatherItem 是 frozen dataclass，
        # 因此複製 list 已足夠。
        try:
            self.gather_queue_settings = (
                self.gather_queue_storage.load(
                    default_settings=(
                        DEFAULT_GATHER_SETTINGS
                    )
                )
            )

        except Exception as error:
            logger.warning(
                f"載入採集排程失敗，"
                f"改用預設排程：{error}"
            )

            self.gather_queue_settings = (
                GatherQueueSettings(
                    items=list(
                        DEFAULT_GATHER_SETTINGS.items
                    ),
                    loop=DEFAULT_GATHER_SETTINGS.loop,
                )
            )

        self.name = "自動採集排程"
        self.description = (
            "按自訂排程順序及時間執行多種生活技能採集"
        )
        self.group_name = "全自動"
        self.group_icon = FluentIcon.PLAY
        self.icon = FluentIcon.PLAY

        # 呢三項仍然屬於 Task 執行參數，
        # 可以保留喺原本設定頁。
        self.default_config.update({
            "最大滾動次數": 8,
            "每次滾動量": -5,
            "畫面等待時間（秒）": 10,
        })

        self.config_description.update({
            "最大滾動次數":
                "在資源列表找不到目標時，"
                "最多向下滾動的次數。",

            "每次滾動量":
                "負數代表向下滾動，"
                "數值絕對值越大，滾動距離越多。",

            "畫面等待時間（秒）":
                "等待生活技能、資源及按鈕出現的最長時間。",

            "編輯採集排程":
                "開啟採集排程編輯視窗，"
                "可新增、刪除、上移、下移及設定循環。",
        })

        self.config_type.update({
            "編輯採集排程": {
                "type": "button",
                "text": "開啟排程編輯器",
                "icon": FluentIcon.SETTING,
                "callback":
                    self.open_gather_queue_dialog,
            },
        })

    def open_gather_queue_dialog(
        self,
    ) -> None:
        """
        打開採集排程編輯視窗。

        保存成功後：
        ・更新目前記憶體設定
        ・寫入 configs/gather_queue.json
        """

        parent = QApplication.activeWindow()

        dialog = GatherQueueDialog(
            settings=self.gather_queue_settings,
            parent=parent,
        )

        result = dialog.exec()

        if result != QDialog.DialogCode.Accepted:
            self.log_info(
                "已取消修改採集排程"
            )
            return

        new_settings = dialog.get_settings()

        try:
            self.gather_queue_storage.save(
                new_settings
            )

        except Exception as error:
            QMessageBox.critical(
                parent,
                "保存失敗",
                f"採集排程無法保存：{error}",
            )
            return

        self.gather_queue_settings = (
            new_settings
        )

        item_count = len(
            self.gather_queue_settings.items
        )

        self.log_info(
            f"採集排程已更新，"
            f"項目數：{item_count}，"
            f"循環執行："
            f"{self.gather_queue_settings.loop}"
        )

        for index, item in enumerate(
            self.gather_queue_settings.items,
            start=1,
        ):
            self.log_info(
                f"排程 {index}："
                f"{item.skill_name} / "
                f"{item.resource_name} / "
                f"{item.duration_minutes} 分鐘 / "
                f"{item.interval_seconds} 秒"
            )

    def run(self):
        DNAOneTimeTask.run(self)

        try:
            return self.do_run()

        except TaskDisabledException:
            self.log_info(
                "任務已手動停止"
            )

        except Exception as error:
            logger.error(
                "AutoGatherTask 執行失敗",
                error,
            )

            self.log_info(
                f"排程執行失敗：{error}"
            )

            raise


    @staticmethod
    def _read_positive_float(
        value: object,
        field_name: str,
    ) -> float:
        """
        將設定值轉換成大於 0 的 float。
        """

        try:
            result = float(value)

        except (
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"{field_name}不是有效數字：{value}"
            ) from error

        if result <= 0:
            raise ValueError(
                f"{field_name}必須大於 0"
            )

        return result

    @staticmethod
    def _read_bool_config(
        value: object,
    ) -> bool:
        """
        安全轉換布林設定。

        避免字串 "False" 被 bool("False")
        錯誤轉換成 True。
        """

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in {
                "true",
                "1",
                "yes",
                "on",
                "開啟",
                "是",
            }:
                return True

            if normalized in {
                "false",
                "0",
                "no",
                "off",
                "關閉",
                "否",
                "",
            }:
                return False

        return bool(value)

    def do_run(self) -> None:
        """
        執行 GatherQueueDialog 保存的採集排程。
        """

        validate_gather_database()

        queue_manager = GatherQueueManager(
            initial_items=(
                self.gather_queue_settings.items
            ),
            loop=(
                self.gather_queue_settings.loop
            ),
        )

        queue_manager.validate_queue()

        if queue_manager.is_empty():
            self.log_info(
                "採集排程為空，"
                "請先按「開啟排程編輯器」"
                "新增採集項目"
            )
            return

        display_rows = (
            queue_manager.to_display_rows()
        )

        self.log_info(
            f"已讀取採集排程，"
            f"項目數：{len(display_rows)}，"
            f"循環執行：{queue_manager.loop}"
        )

        for row in display_rows:
            self.log_info(
                f"排程 {row['order']}："
                f"{row['skill_name']} / "
                f"{row['resource_name']} / "
                f"{row['duration_minutes']} 分鐘 / "
                f"每 {row['interval_seconds']} 秒重新操作"
            )

        cycle_number = 0

        while True:
            cycle_number += 1

            queue = queue_manager.get_items()

            self.log_info(
                f"開始第 {cycle_number} 次排程循環，"
                f"項目數：{len(queue)}"
            )

            for index, gather_item in enumerate(
                queue,
                start=1,
            ):
                self.log_info(
                    f"開始第 {index}/{len(queue)} 個採集項目："
                    f"{gather_item.skill_name} / "
                    f"{gather_item.resource_name}"
                )

                self.run_gather_item(
                    gather_item
                )

            if not queue_manager.loop:
                break

            self.log_info(
                "本次排程已完成，循環執行已啟用，"
                "即將由第一項重新開始"
            )

        self.log_info(
            "所有採集排程已完成"
        )

    def run_gather_item(
        self,
        gather_item: GatherItem,
    ) -> None:
        """
        在指定時間內，
        重複執行一個採集項目。
        """

        start_time = time.monotonic()

        end_time = (
            start_time
            + gather_item.duration_minutes * 60
        )

        round_number = 0

        self.log_info(
            f"開始採集："
            f"{gather_item.skill_name} / "
            f"{gather_item.resource_name}，"
            f"執行 {gather_item.duration_minutes} 分鐘"
        )

        while time.monotonic() < end_time:
            round_number += 1
            round_start_time = time.monotonic()

            self.log_info(
                f"{gather_item.resource_name}："
                f"開始第 {round_number} 輪"
            )

            try:
                self.execute_one_round(
                    gather_item
                )

            except TaskDisabledException:
                raise

            except Exception as error:
                logger.warning(
                    f"{gather_item.resource_name} "
                    f"第 {round_number} 輪失敗：{error}"
                )

                self.log_info(
                    f"{gather_item.resource_name} "
                    f"第 {round_number} 輪失敗，"
                    f"嘗試返回主畫面"
                )

                self.close_opened_windows()

            remaining_time = (
                end_time - time.monotonic()
            )

            if remaining_time <= 0:
                break

            round_elapsed = (
                time.monotonic()
                - round_start_time
            )

            wait_seconds = max(
                0,
                gather_item.interval_seconds
                - round_elapsed,
            )

            wait_seconds = min(
                wait_seconds,
                remaining_time,
            )

            if wait_seconds > 0:
                self.log_info(
                    f"等待 {wait_seconds:.1f} 秒後"
                    f"開始下一輪"
                )

                self.sleep_with_progress(
                    wait_seconds
                )

        self.log_info(
            f"已完成："
            f"{gather_item.skill_name} / "
            f"{gather_item.resource_name}"
        )

    def execute_one_round(
        self,
        gather_item: GatherItem,
    ) -> None:
        """
        執行一次完整採集流程。

        每一輪開始前會先確認目前位於遊戲主畫面。
        如果唔係主畫面，會嘗試逐次按 ESC 返回。
        確認主畫面後先開始按 C。
        """

        timeout = float(
            self.config.get(
                "畫面等待時間（秒）",
                10,
            )
        )

        skill_definition = get_skill_definition(
            gather_item.skill_name
        )

        resource_definition = get_resource_definition(
            gather_item.skill_name,
            gather_item.resource_name,
        )

        self.log_info(
            f"Database 已解析："
            f"{skill_definition.name}"
            f"({skill_definition.feature}) / "
            f"{resource_definition.name}"
            f"({resource_definition.feature})"
        )

        # =========================================================
        # 0. 每一輪開始前先確認目前係遊戲主畫面
        # =========================================================

        self.log_info(
            "每輪開始前確認遊戲主畫面"
        )

        main_screen_ready = (
            self.main_screen_page.ensure_visible(
                max_escape_attempts=5,
                detection_timeout=2.0,
                after_escape_sleep=0.8,
                threshold=0.8,
            )
        )

        if not main_screen_ready:
            raise RuntimeError(
                "每輪開始前無法確認遊戲主畫面，"
                "本輪停止執行"
            )

        self.log_info(
            "已確認目前位於遊戲主畫面，"
            "開始執行採集流程"
        )

        # =========================================================
        # 1. 打開角色資訊頁
        # =========================================================

        self.character_page.open(
            after_sleep=1.5,
        )

        # =========================================================
        # 2. 進入生活技能頁
        # =========================================================

        self.life_skill_page.open(
            timeout=timeout,
            after_sleep=1.5,
        )

        # =========================================================
        # 3. 選擇生活技能
        # =========================================================

        self.life_skill_page.select_skill(
            skill_name=skill_definition.name,
            skill_feature=skill_definition.feature,
            timeout=timeout,
            after_sleep=1.5,
        )

        # =========================================================
        # 4. 搜尋並選擇採集資源
        # =========================================================

        self.gather_page.select_resource(
            resource_name=resource_definition.name,
            resource_feature=resource_definition.feature,
            competing_resource_features=tuple(
                definition.feature
                for name, definition in skill_definition.resources.items()
                if name != resource_definition.name
            ),
            after_sleep=1.0,
        )

        # =========================================================
        # 5. 點擊「尋找附近位置」
        # =========================================================

        self.gather_page.find_nearby(
            timeout=timeout,
            after_sleep=2.0,
        )

        self.log_info(
            "本輪採集操作已完成"
        )

    def release_game_keys(self) -> None:
        """
        任務停止或發生例外時，
        釋放可能殘留的按鍵。
        """

        try:
            self.ensure_in_front()
            self.sleep(0.1)

            for key in (
                "c",
                "esc",
                "w",
                "a",
                "s",
                "d",
            ):
                self.pydirect_interaction.send_key_up(
                    key
                )

            self.log_info(
                "已清理鍵盤按下狀態"
            )

        except Exception as error:
            logger.warning(
                f"清理鍵盤狀態失敗：{error}"
            )

    def press_game_key(
        self,
        key: str,
        down_time: float = 0.08,
        after_sleep: float = 0.5,
    ) -> None:
        """
        使用目前 Task interaction 發送按鍵。
        """

        self.log_info(
            f"發送按鍵：{key}"
        )

        self.send_key(
            key,
            down_time=down_time,
            after_sleep=after_sleep,
        )

    def move_and_click_box(
        self,
        box,
        after_sleep: float = 1.0,
        hover_sleep: float = 0.2,
    ) -> None:
        """
        將遊戲切換到前景，
        再將滑鼠移到辨識結果中央並點擊。
        """

        center_x = int(
            box.x + box.width / 2
        )
        center_y = int(
            box.y + box.height / 2
        )

        self.ensure_in_front()
        self.sleep(0.3)

        self.log_info(
            f"移動滑鼠到 {box.name} 中央："
            f"({center_x}, {center_y})"
        )

        self.pydirect_interaction.move(
            center_x,
            center_y,
        )

        self.sleep(
            hover_sleep
        )

        self.pydirect_interaction.click(
            down_time=0.1,
        )

        self.log_info(
            f"已點擊 {box.name}："
            f"({center_x}, {center_y})"
        )

        self.sleep(
            after_sleep
        )

    def focus_game_window(self) -> None:
        """
        將遊戲視窗切到前景，
        並點擊標題列取得鍵盤焦點。
        """

        window_title = "瑪奇 Mobile"

        hwnd = win32gui.FindWindow(
            None,
            window_title,
        )

        if not hwnd:
            raise RuntimeError(
                f"找不到遊戲視窗："
                f"{window_title}"
            )

        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(
                hwnd,
                win32con.SW_RESTORE,
            )

            self.sleep(0.5)

        self.ensure_in_front()
        self.sleep(0.8)

        (
            window_left,
            window_top,
            window_right,
            _,
        ) = win32gui.GetWindowRect(
            hwnd
        )

        _, client_top = (
            win32gui.ClientToScreen(
                hwnd,
                (0, 0),
            )
        )

        title_bar_height = (
            client_top - window_top
        )

        if title_bar_height <= 0:
            self.log_info(
                "遊戲視窗沒有可點擊的標題列，"
                "只切換到前景"
            )
            return

        title_x = (
            window_left
            + int(
                (
                    window_right
                    - window_left
                )
                * 0.40
            )
        )

        title_y = (
            window_top
            + max(
                5,
                title_bar_height // 2,
            )
        )

        self.log_info(
            f"點擊遊戲標題列取得焦點："
            f"({title_x}, {title_y})"
        )

        win32api.SetCursorPos(
            (title_x, title_y)
        )

        self.sleep(0.15)

        win32api.mouse_event(
            win32con.MOUSEEVENTF_LEFTDOWN,
            0,
            0,
            0,
            0,
        )

        self.sleep(0.05)

        win32api.mouse_event(
            win32con.MOUSEEVENTF_LEFTUP,
            0,
            0,
            0,
            0,
        )

        self.sleep(0.5)

    def wait_and_click(
        self,
        feature_name: str,
        timeout: float,
        threshold: float = 0.8,
        after_sleep: float = 1.0,
    ):
        """
        等待指定 Template 出現，
        然後先將滑鼠移到素材中央，再點擊。
        """

        box = self.wait_until(
            lambda: self.find_one(
                feature_name,
                threshold=threshold,
            ),
            time_out=timeout,
            raise_if_not_found=False,
        )

        if box is None:
            raise RuntimeError(
                f"等待逾時，找不到圖片素材："
                f"{feature_name}"
            )

        self.log_info(
            f"已找到圖片素材："
            f"{feature_name}，"
            f"confidence={box.confidence}"
        )

        self.move_and_click_box(
            box,
            after_sleep=after_sleep,
        )

        return box

    def find_resource(
        self,
        feature_name: str,
        competing_feature_names: tuple[str, ...] = (),
    ):
        """
        在右側資源列表中尋找指定資源。

        找不到時會將實體滑鼠移到列表，
        再使用滾輪向下捲動。
        """

        max_scroll_attempts = int(
            self.config.get(
                "最大滾動次數",
                8,
            )
        )

        scroll_amount = int(
            self.config.get(
                "每次滾動量",
                -5,
            )
        )

        scroll_x = int(
            self.width * 0.78
        )
        scroll_y = int(
            self.height * 0.60
        )

        for attempt in range(
            max_scroll_attempts + 1
        ):
            resource_box = self.find_one(
                feature_name=feature_name,
                horizontal_variance=0.05,
                vertical_variance=0.15,
                threshold=0.8,
            )

            if resource_box is not None:
                conflicting_box = self.find_conflicting_resource(
                    resource_box,
                    competing_feature_names,
                )
                if conflicting_box is not None:
                    self.log_info(
                        f"Reject resource match {resource_box.name}="
                        f"{resource_box.confidence:.4f}; "
                        f"same row is {conflicting_box.name}="
                        f"{conflicting_box.confidence:.4f}"
                    )
                    resource_box = None

            if resource_box is not None:
                self.log_info(
                    f"已找到資源 "
                    f"{feature_name}，"
                    f"搜尋次數："
                    f"{attempt + 1}"
                )

                return resource_box

            if attempt >= max_scroll_attempts:
                break

            self.log_info(
                f"未找到資源 "
                f"{feature_name}，"
                f"向下滾動 "
                f"({attempt + 1}/"
                f"{max_scroll_attempts})"
            )

            self.ensure_in_front()
            self.sleep(0.2)

            self.pydirect_interaction.scroll(
                scroll_x,
                scroll_y,
                scroll_amount,
            )

            self.sleep(1.0)

        return None

    def find_conflicting_resource(
        self,
        target_box,
        competing_feature_names: tuple[str, ...],
        confidence_margin: float = 0.01,
    ):
        search_box = Box(
            max(0, target_box.x - 120),
            max(0, target_box.y - 20),
            target_box.width + 240,
            target_box.height + 40,
        )

        for feature_name in competing_feature_names:
            try:
                box = self.find_one(
                    feature_name=feature_name,
                    box=search_box,
                    threshold=0.8,
                )
            except Exception:
                continue

            if box is None:
                continue

            if (
                box.confidence
                >= target_box.confidence + confidence_margin
            ):
                return box

        return None

    def close_opened_windows(
        self,
    ) -> bool:
        """
        發生錯誤後嘗試返回遊戲主畫面。

        舊做法：
            固定按兩次 ESC。

        新做法：
            先偵測主畫面。
            唔係主畫面先逐次按 ESC。
            每按一次都重新偵測。
        """

        self.log_info(
            "開始確認並嘗試返回遊戲主畫面"
        )

        success = self.main_screen_page.ensure_visible(
            max_escape_attempts=5,
            detection_timeout=2.0,
            after_escape_sleep=0.8,
            threshold=0.8,
        )

        if success:
            self.log_info(
                "已確認返回遊戲主畫面"
            )
            return True

        logger.warning(
            "多次按 ESC 後仍然無法確認主畫面"
        )

        self.log_info(
            "多次按 ESC 後仍然無法確認主畫面"
        )

        return False

    def sleep_with_progress(
        self,
        total_seconds: float,
    ) -> None:
        """
        分段等待，方便 GUI 隨時停止任務。
        """

        end_time = (
            time.monotonic()
            + total_seconds
        )

        while True:
            remaining = (
                end_time
                - time.monotonic()
            )

            if remaining <= 0:
                return

            self.sleep(
                min(
                    1.0,
                    remaining,
                )
            )
