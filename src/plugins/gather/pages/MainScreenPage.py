from typing import Any


class MainScreenPage:
    """
    遊戲主畫面狀態偵測。

    目前使用單一 Template：
        main_screen_marker_leftdown

    用途：
    1. 判斷目前是否位於主畫面
    2. 等待主畫面出現
    3. 如果目前唔係主畫面，逐次按 ESC 返回
    """

    MAIN_SCREEN_FEATURE = "main_screen_marker_leftdown"

    def __init__(
        self,
        task: Any,
    ) -> None:
        self.task = task

    def is_visible(
        self,
        threshold: float = 0.8,
    ) -> bool:
        """
        判斷目前是否為主畫面。

        Returns:
            True:
                找到主畫面 Template。

            False:
                找不到主畫面 Template。
        """

        box = self.task.find_one(
            feature_name=self.MAIN_SCREEN_FEATURE,
            horizontal_variance=0.01,
            vertical_variance=0.01,
            threshold=threshold,
        )

        if box is None:
            return False

        self.task.log_info(
            f"已偵測到主畫面："
            f"{self.MAIN_SCREEN_FEATURE}，"
            f"confidence={box.confidence}"
        )

        return True

    def wait_until_visible(
        self,
        timeout: float = 5.0,
        threshold: float = 0.8,
    ) -> bool:
        """
        等待主畫面出現。

        適合：
        ・按 ESC 後等待畫面切換
        ・點擊「尋找附近位置」後等待返回主畫面
        """

        result = self.task.wait_until(
            lambda: self.is_visible(
                threshold=threshold,
            ),
            time_out=timeout,
            raise_if_not_found=False,
        )

        return bool(result)

    def ensure_visible(
        self,
        max_escape_attempts: int = 5,
        detection_timeout: float = 2.0,
        after_escape_sleep: float = 0.8,
        threshold: float = 0.8,
    ) -> bool:
        """
        確保目前返回遊戲主畫面。

        流程：

        1. 先檢查目前是否已經係主畫面
        2. 如果係，唔按 ESC
        3. 如果唔係，按一次 ESC
        4. 等待主畫面 Template
        5. 仲未出現就再按一次 ESC
        6. 最多重試 max_escape_attempts 次

        Returns:
            True:
                已確認返回主畫面。

            False:
                多次嘗試後仍然未確認主畫面。
        """

        self.task.log_info(
            "檢查目前是否位於遊戲主畫面"
        )

        # 第一次先直接檢查。
        # 已經係主畫面就唔應該再按 ESC，
        # 否則有機會反而打開遊戲選單。
        if self.is_visible(
            threshold=threshold,
        ):
            self.task.log_info(
                "目前已經係遊戲主畫面，"
                "不需要按 ESC"
            )
            return True

        for attempt in range(
            1,
            max_escape_attempts + 1,
        ):
            self.task.log_info(
                f"目前未偵測到主畫面，"
                f"嘗試按 ESC "
                f"({attempt}/{max_escape_attempts})"
            )

            try:
                # 確保遊戲取得焦點。
                self.task.focus_game_window()
            except Exception as error:
                self.task.log_info(
                    f"切換遊戲前景失敗：{error}"
                )

            self.task.press_game_key(
                "esc",
                down_time=0.08,
                after_sleep=after_escape_sleep,
            )

            # ESC 後唔係立即判定，
            # 因為遊戲可能有關閉視窗動畫。
            if self.wait_until_visible(
                timeout=detection_timeout,
                threshold=threshold,
            ):
                self.task.log_info(
                    f"按 ESC {attempt} 次後，"
                    f"已確認返回遊戲主畫面"
                )
                return True

        self.task.log_info(
            f"已嘗試按 ESC "
            f"{max_escape_attempts} 次，"
            f"仍然未能確認主畫面"
        )

        return False