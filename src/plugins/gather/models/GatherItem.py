from dataclasses import dataclass


@dataclass(frozen=True)
class GatherItem:
    """
    採集排程中的一個項目。

    skill_name:
        使用者選擇的生活技能，例如「採礦」。

    resource_name:
        使用者選擇的資源，例如「銅礦脈」。

    duration_minutes:
        此採集項目持續執行幾多分鐘。

    interval_seconds:
        每隔幾多秒重新執行一次採集流程。

    Template feature 不保存在 GatherItem。
    AutoGatherTask 會根據 skill_name 及 resource_name，
    自動向 gather_database.py 查詢。
    """

    skill_name: str
    resource_name: str
    duration_minutes: float
    interval_seconds: float = 60.0

    def __post_init__(self) -> None:
        if not self.skill_name.strip():
            raise ValueError(
                "skill_name 不可以為空"
            )

        if not self.resource_name.strip():
            raise ValueError(
                "resource_name 不可以為空"
            )

        if self.duration_minutes <= 0:
            raise ValueError(
                "duration_minutes 必須大於 0"
            )

        if self.interval_seconds <= 0:
            raise ValueError(
                "interval_seconds 必須大於 0"
            )