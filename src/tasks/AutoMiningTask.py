import win32api # type: ignore[import-untyped]
import win32con # type: ignore[import-untyped]
import win32gui # type: ignore[import-untyped]

import time

from qfluentwidgets import FluentIcon

from ok import Logger, TaskDisabledException
from src.tasks.BaseDNATask import BaseDNATask
from src.tasks.DNAOneTimeTask import DNAOneTimeTask


logger = Logger.get_logger(__name__)


class AutoMiningTask(DNAOneTimeTask, BaseDNATask):
    """
    自動重複採礦。

    流程：
    1. 按 C 打開角色資訊
    2. 點擊「生活技能」
    3. 點擊「採礦」
    4. 在右側礦物列表尋找「銅礦脈」
    5. 找不到時向下滾動
    6. 點擊「銅礦脈」
    7. 點擊「尋找附近位置」
    8. 返回主畫面後等待下一輪
    """

    LIFE_SKILL_FEATURE = "life_skill_menu"
    MINING_SKILL_FEATURE = "mining_skill"
    COPPER_ORE_FEATURE = "copper_ore_item"
    FIND_NEARBY_FEATURE = "find_nearby_location"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 避免背景執行滑鼠抖動、按鍵或其他輸入，干擾本 Task。
        self.enable_fidget_action = False

        self.name = "自動重複採礦"
        self.description = "每隔指定時間重新尋找銅礦脈並開始自動採集"
        self.group_name = "全自動"
        self.group_icon = FluentIcon.PLAY
        self.icon = FluentIcon.PLAY

        self.default_config.update({
            # 整個任務運行幾多分鐘
            "執行時間（分鐘）": 60,

            # 每輪由開始計算，隔幾多秒再重新操作
            "每輪間隔（秒）": 60,

            # 尋找銅礦時最多向下滾動幾次
            "最大滾動次數": 8,

            # 每次滾輪向下嘅幅度
            "每次滾動量": -5,

            # 每個畫面最多等待幾多秒
            "畫面等待時間（秒）": 10,
        })

        self.config_description.update({
            "執行時間（分鐘）":
                "任務總運行時間。到達設定分鐘數後自動停止。",

            "每輪間隔（秒）":
                "每輪開始時間之間的間隔。建議先設定為60秒。",

            "最大滾動次數":
                "在採礦物列表找不到銅礦脈時，最多向下滾動的次數。",

            "每次滾動量":
                "負數代表向下滾動，數值絕對值越大，滾動距離越多。",

            "畫面等待時間（秒）":
                "等待生活技能、採礦等畫面出現的最長時間。",
        })

    def release_game_keys(self):
        """
        任務停止或發生例外時，釋放可能殘留的按鍵。
        """

        try:
            self.ensure_in_front()
            self.sleep(0.1)

            for key in ("c", "esc", "w", "a", "s", "d"):
                self.pydirect_interaction.send_key_up(key)

            self.log_info("已清理鍵盤按下狀態")

        except Exception as error:
            logger.warning(f"清理鍵盤狀態失敗：{error}")

    def run(self):
        DNAOneTimeTask.run(self)

        try:
            return self.do_run()

        except TaskDisabledException:
            self.log_info("任務已手動停止")

        except Exception as error:
            logger.error("AutoMiningTask 執行失敗", error)
            raise


    def do_run(self):
        duration_minutes = float(
            self.config.get("執行時間（分鐘）", 60)
        )
        interval_seconds = float(
            self.config.get("每輪間隔（秒）", 60)
        )

        task_start_time = time.monotonic()
        task_end_time = task_start_time + duration_minutes * 60

        round_number = 0

        self.log_info(
            f"開始自動採礦，總執行時間：{duration_minutes} 分鐘，"
            f"每輪間隔：{interval_seconds} 秒"
        )

        while time.monotonic() < task_end_time:
            round_number += 1
            round_start_time = time.monotonic()

            self.log_info(f"開始第 {round_number} 輪採礦")

            try:
                self.execute_one_round()
                self.log_info(f"第 {round_number} 輪操作完成")
            except Exception as error:
                # 某一輪失敗時唔立即結束整個任務。
                # 等待下一輪重新由主畫面開始再試。
                logger.warning(
                    f"第 {round_number} 輪操作失敗：{error}"
                )
                self.log_info(
                    f"第 {round_number} 輪失敗，稍後重新嘗試"
                )

                # 嘗試按 ESC 關閉殘留視窗，避免下一輪卡住。
                self.close_opened_windows()

            remaining_task_time = task_end_time - time.monotonic()

            if remaining_task_time <= 0:
                break

            # 每輪間隔係由「本輪開始時間」計算，
            # 避免操作時間加埋 sleep，令每輪變成超過60秒。
            round_elapsed = time.monotonic() - round_start_time
            wait_seconds = max(0, interval_seconds - round_elapsed)

            # 唔等待超過整個任務剩餘時間。
            wait_seconds = min(wait_seconds, remaining_task_time)

            if wait_seconds > 0:
                self.log_info(
                    f"等待 {wait_seconds:.1f} 秒後開始下一輪"
                )
                self.sleep_with_progress(wait_seconds)

        self.log_info(
            f"已到達設定時間，共執行 {round_number} 輪，任務結束"
        )

    def press_game_key(
        self,
        key: str,
        down_time: float = 0.08,
        after_sleep: float = 0.5,
    ):
        """
        使用 Task 目前設定的 interaction 發送按鍵。
        """

        self.log_info(f"發送按鍵：{key}")

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
    ):
        """
        將遊戲切換到前景，
        再將滑鼠移到辨識結果中央並點擊。
        """

        center_x = int(box.x + box.width / 2)
        center_y = int(box.y + box.height / 2)

        # PyDirectInteraction 只會在遊戲是前景時操作。
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

        self.sleep(hover_sleep)

        self.pydirect_interaction.click(
            down_time=0.1,
        )

        self.log_info(
            f"已點擊 {box.name}："
            f"({center_x}, {center_y})"
        )

        self.sleep(after_sleep)

    def focus_game_window(self):
        """
        將遊戲視窗切到前景，並點擊標題列取得鍵盤焦點。

        點擊標題列而唔係遊戲內容區，可以避免：
        ・移動遊戲視角
        ・選中場景目標
        ・中斷自動採集
        ・誤點遊戲 UI
        """

        window_title = "瑪奇 Mobile"

        hwnd = win32gui.FindWindow(None, window_title)

        if not hwnd:
            raise RuntimeError(
                f"找不到遊戲視窗：{window_title}"
            )

        # 如果遊戲最小化，先還原視窗。
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(
                hwnd,
                win32con.SW_RESTORE,
            )
            self.sleep(0.5)

        # 先要求 Windows 將遊戲切到前景。
        self.ensure_in_front()
        self.sleep(0.8)

        # 整個視窗外框座標，包括標題列。
        window_left, window_top, window_right, _ = (
            win32gui.GetWindowRect(hwnd)
        )

        # 遊戲內容區左上角的螢幕座標。
        client_left, client_top = win32gui.ClientToScreen(
            hwnd,
            (0, 0),
        )

        # 標題列高度大約等於：
        # client area 頂部 - window frame 頂部。
        title_bar_height = client_top - window_top

        if title_bar_height <= 0:
            # 無邊框／全螢幕模式可能冇標題列。
            # 呢種情況只使用 ensure_in_front，不執行點擊。
            self.log_info(
                "遊戲視窗沒有可點擊的標題列，只切換到前景"
            )
            return

        # 點擊標題列中央偏左位置，
        # 避免右上角最小化、最大化及關閉按鈕。
        title_x = window_left + int(
            (window_right - window_left) * 0.40
        )
        title_y = window_top + max(
            5,
            title_bar_height // 2,
        )

        self.log_info(
            f"點擊遊戲標題列取得焦點："
            f"({title_x}, {title_y})"
        )

        # 標題列座標係螢幕絕對座標，
        # 所以直接使用 Win32 API 移動及點擊。
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

    def execute_one_round(self):
        timeout = float(
            self.config.get("畫面等待時間（秒）", 10)
        )

        self.log_info("將遊戲視窗切換到前景並取得鍵盤焦點")
        self.focus_game_window()

        self.log_info("按 C 打開角色資訊")
        self.press_game_key(
            "c",
            down_time=0.08,
            after_sleep=1.5,
        )

        self.log_info("等待並點擊「生活技能」")
        self.wait_and_click(
            feature_name=self.LIFE_SKILL_FEATURE,
            timeout=timeout,
            after_sleep=1.5,
        )

        self.log_info("等待並點擊「採礦」")
        self.wait_and_click(
            feature_name=self.MINING_SKILL_FEATURE,
            timeout=timeout,
            after_sleep=1.5,
        )

        self.log_info("尋找「銅礦脈」")
        copper_ore_box = self.find_copper_ore()

        if copper_ore_box is None:
            raise RuntimeError(
                "滾動列表後仍然找不到 copper_ore_item"
            )

        self.log_info("點擊「銅礦脈」")
        self.move_and_click_box(
            copper_ore_box,
            after_sleep=1.0,
        )

        self.log_info("等待並點擊「尋找附近位置」")
        self.wait_and_click(
            feature_name=self.FIND_NEARBY_FEATURE,
            timeout=timeout,
            after_sleep=2.0,
        )

        # 點擊後遊戲返回主畫面，角色開始自動尋路及採集。
        self.log_info("已開始自動尋路及採集")

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
                f"等待逾時，找不到圖片素材：{feature_name}"
            )

        self.log_info(
            f"已找到圖片素材：{feature_name}，"
            f"confidence={box.confidence}"
        )

        self.move_and_click_box(
            box,
            after_sleep=after_sleep,
        )

        return box

    def find_copper_ore(self):
        """
        在右側採礦物列表內尋找銅礦脈。

        找不到時，將遊戲切到前景，
        將實體滑鼠移到右側列表，再使用真實滾輪向下捲動。
        """

        max_scroll_attempts = int(
            self.config.get("最大滾動次數", 8)
        )
        scroll_amount = int(
            self.config.get("每次滾動量", -5)
        )

        # 相對於遊戲畫面的右側礦物列表中央位置。
        scroll_x = int(self.width * 0.78)
        scroll_y = int(self.height * 0.60)

        for attempt in range(max_scroll_attempts + 1):
            copper_ore_box = self.find_one(
                self.COPPER_ORE_FEATURE,
                threshold=0.8,
            )

            if copper_ore_box is not None:
                self.log_info(
                    f"已找到銅礦脈，搜尋次數：{attempt + 1}"
                )
                return copper_ore_box

            if attempt >= max_scroll_attempts:
                break

            self.log_info(
                f"未找到銅礦脈，向下滾動 "
                f"({attempt + 1}/{max_scroll_attempts})，"
                f"位置：({scroll_x}, {scroll_y})"
            )

            # PyDirect 滾輪要求遊戲在前景。
            self.ensure_in_front()
            self.sleep(0.2)

            # 會先將實體滑鼠移到列表位置，再滾動。
            self.pydirect_interaction.scroll(
                scroll_x,
                scroll_y,
                scroll_amount,
            )

            # 等待列表動畫及畫面更新。
            self.sleep(1.0)

        return None

    def close_opened_windows(self):
        """
        本輪失敗後嘗試關閉目前視窗。
        測試期間只按一次 ESC，避免連續輸入干擾排查。
        """

        self.press_game_key(
            "esc",
            down_time=0.08,
            after_sleep=0.5,
        )

    def sleep_with_progress(self, total_seconds: float):
        """
        分段等待，避免一次 sleep 太長，
        同時方便使用者隨時喺 GUI 停止任務。
        """

        end_time = time.monotonic() + total_seconds

        while True:
            remaining = end_time - time.monotonic()

            if remaining <= 0:
                return

            self.sleep(min(1.0, remaining))