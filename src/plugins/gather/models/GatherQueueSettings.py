from dataclasses import dataclass, field

from src.plugins.gather.models.GatherItem import (
    GatherItem,
)


@dataclass
class GatherQueueSettings:
    """
    採集排程整體設定。

    items:
        按順序執行的採集項目。

    loop:
        True：
            全部項目完成後，由第一項重新開始。

        False：
            全部項目完成後結束任務。
    """

    items: list[GatherItem] = field(
        default_factory=list
    )

    loop: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.items, list):
            raise TypeError(
                "items 必須為 list[GatherItem]"
            )

        for index, item in enumerate(
            self.items,
            start=1,
        ):
            if not isinstance(item, GatherItem):
                raise TypeError(
                    f"第 {index} 個排程項目"
                    f"不是 GatherItem"
                )