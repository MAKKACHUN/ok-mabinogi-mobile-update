from typing import Any


class CharacterPage:
    """
    角色資訊頁面。

    職責：
    1. 將遊戲切換到前景
    2. 取得鍵盤焦點
    3. 按 C 打開角色資訊頁
    4. 使用 ESC 關閉目前頁面
    """

    def __init__(self, task: Any):
        """
        Args:
            task:
                AutoGatherTask 實例。

                Page Object 會使用 Task 已有的：
                - focus_game_window()
                - press_game_key()
                - log_info()
        """
        self.task = task

    def open(
        self,
        after_sleep: float = 1.5,
    ) -> None:
        """
        打開角色資訊頁面。
        """

        self.task.log_info(
            "將遊戲視窗切換到前景並取得鍵盤焦點"
        )

        self.task.focus_game_window()

        self.task.log_info(
            "按 C 打開角色資訊"
        )

        self.task.press_game_key(
            "c",
            down_time=0.08,
            after_sleep=after_sleep,
        )

    def close(
        self,
        after_sleep: float = 0.5,
    ) -> None:
        """
        使用 ESC 關閉目前頁面。
        """

        self.task.log_info(
            "按 ESC 關閉目前頁面"
        )

        self.task.press_game_key(
            "esc",
            down_time=0.08,
            after_sleep=after_sleep,
        )