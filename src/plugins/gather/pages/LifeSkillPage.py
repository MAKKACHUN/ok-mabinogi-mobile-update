from typing import Any


class LifeSkillPage:
    """
    生活技能頁面。

    職責：
    1. 在角色資訊頁中點擊「生活技能」
    2. 選擇指定生活技能，例如：
       - 採礦
       - 剪羊毛
       - 伐木
       - 採集藥草
    """

    LIFE_SKILL_MENU_FEATURE = "life_skill_menu"

    def __init__(self, task: Any):
        """
        Args:
            task:
                AutoGatherTask 實例。

                Page Object 會使用 Task 已有的：
                - wait_and_click()
                - log_info()
        """
        self.task = task

    def open(
        self,
        timeout: float,
        after_sleep: float = 1.5,
    ) -> None:
        """
        點擊角色資訊頁左側的「生活技能」。
        """

        self.task.log_info(
            "等待並點擊「生活技能」"
        )

        self.task.wait_and_click(
            feature_name=self.LIFE_SKILL_MENU_FEATURE,
            timeout=timeout,
            threshold=0.8,
            after_sleep=after_sleep,
        )

    def select_skill(
        self,
        skill_name: str,
        skill_feature: str,
        timeout: float,
        after_sleep: float = 1.5,
    ) -> None:
        """
        選擇指定生活技能。

        Args:
            skill_name:
                顯示於 log 的技能名稱，例如「採礦」。

            skill_feature:
                Template 名稱，例如「mining_skill」。

            timeout:
                最多等待幾多秒。

            after_sleep:
                點擊後等待幾多秒。
        """

        self.task.log_info(
            f"等待並點擊生活技能："
            f"「{skill_name}」"
        )

        self.task.wait_and_click(
            feature_name=skill_feature,
            timeout=timeout,
            threshold=0.8,
            after_sleep=after_sleep,
        )