from collections.abc import Iterable

from src.plugins.gather.data.gather_database import (
    get_resource_definition,
    get_skill_definition,
)
from src.plugins.gather.models.GatherItem import (
    GatherItem,
)
from src.plugins.gather.models.GatherQueueSettings import (
    GatherQueueSettings,
)


class GatherQueueManager:
    """
    採集排程管理器。

    負責：
    ・新增排程
    ・刪除排程
    ・上移／下移
    ・清空排程
    ・循環設定
    ・驗證技能及資源
    ・向 Task 提供安全的 Queue 副本

    index 全部使用 Python 的 0 起始索引。
    """

    def __init__(
        self,
        initial_items: Iterable[GatherItem] | None = None,
        loop: bool = False,
    ) -> None:
        self._settings = GatherQueueSettings(
            items=[],
            loop=bool(loop),
        )

        if initial_items is not None:
            self.replace_all(initial_items)

    @property
    def loop(self) -> bool:
        """
        取得循環設定。
        """

        return self._settings.loop

    def set_loop(
        self,
        enabled: bool,
    ) -> None:
        """
        設定全部項目完成後是否循環執行。
        """

        self._settings.loop = bool(enabled)

    def get_items(self) -> list[GatherItem]:
        """
        取得 Queue 副本。

        回傳新 list，避免外部程式直接修改
        Manager 內部的 Queue。
        """

        return list(self._settings.items)

    def get_item(
        self,
        index: int,
    ) -> GatherItem:
        """
        取得指定位置的排程項目。
        """

        self._validate_index(index)

        return self._settings.items[index]

    def count(self) -> int:
        """
        取得排程項目數量。
        """

        return len(self._settings.items)

    def is_empty(self) -> bool:
        """
        判斷排程是否為空。
        """

        return not self._settings.items

    def add(
        self,
        skill_name: str,
        resource_name: str,
        duration_minutes: float,
        interval_seconds: float = 60.0,
    ) -> GatherItem:
        """
        在 Queue 最後新增一個採集項目。
        """

        item = self.create_item(
            skill_name=skill_name,
            resource_name=resource_name,
            duration_minutes=duration_minutes,
            interval_seconds=interval_seconds,
        )

        self._settings.items.append(item)

        return item

    def insert(
        self,
        index: int,
        skill_name: str,
        resource_name: str,
        duration_minutes: float,
        interval_seconds: float = 60.0,
    ) -> GatherItem:
        """
        在指定位置插入採集項目。

        允許 index 等於目前 Queue 長度，
        即插入到最後。
        """

        self._validate_insert_index(index)

        item = self.create_item(
            skill_name=skill_name,
            resource_name=resource_name,
            duration_minutes=duration_minutes,
            interval_seconds=interval_seconds,
        )

        self._settings.items.insert(
            index,
            item,
        )

        return item

    def update(
        self,
        index: int,
        skill_name: str,
        resource_name: str,
        duration_minutes: float,
        interval_seconds: float = 60.0,
    ) -> GatherItem:
        """
        更新指定位置的採集項目。
        """

        self._validate_index(index)

        item = self.create_item(
            skill_name=skill_name,
            resource_name=resource_name,
            duration_minutes=duration_minutes,
            interval_seconds=interval_seconds,
        )

        self._settings.items[index] = item

        return item

    def remove(
        self,
        index: int,
    ) -> GatherItem:
        """
        刪除並回傳指定位置的項目。
        """

        self._validate_index(index)

        return self._settings.items.pop(index)

    def clear(self) -> None:
        """
        清空全部排程。
        """

        self._settings.items.clear()

    def move_up(
        self,
        index: int,
    ) -> int:
        """
        將指定項目向上移一格。

        Returns:
            移動後的新 index。

        第一項再向上移時不會報錯，
        直接維持 index 0。
        """

        self._validate_index(index)

        if index == 0:
            return 0

        new_index = index - 1

        self._settings.items[index], (
            self._settings.items[new_index]
        ) = (
            self._settings.items[new_index],
            self._settings.items[index],
        )

        return new_index

    def move_down(
        self,
        index: int,
    ) -> int:
        """
        將指定項目向下移一格。

        Returns:
            移動後的新 index。

        最後一項再向下移時不會報錯，
        直接維持原 index。
        """

        self._validate_index(index)

        last_index = len(
            self._settings.items
        ) - 1

        if index >= last_index:
            return last_index

        new_index = index + 1

        self._settings.items[index], (
            self._settings.items[new_index]
        ) = (
            self._settings.items[new_index],
            self._settings.items[index],
        )

        return new_index

    def replace_all(
        self,
        items: Iterable[GatherItem],
    ) -> None:
        """
        使用指定項目完整取代目前 Queue。
        """

        validated_items: list[GatherItem] = []

        for index, item in enumerate(
            items,
            start=1,
        ):
            if not isinstance(item, GatherItem):
                raise TypeError(
                    f"第 {index} 個項目"
                    f"不是 GatherItem"
                )

            self.validate_item(item)
            validated_items.append(item)

        self._settings.items = validated_items

    def create_item(
        self,
        skill_name: str,
        resource_name: str,
        duration_minutes: float,
        interval_seconds: float = 60.0,
    ) -> GatherItem:
        """
        驗證輸入並建立 GatherItem。
        """

        item = GatherItem(
            skill_name=skill_name,
            resource_name=resource_name,
            duration_minutes=float(
                duration_minutes
            ),
            interval_seconds=float(
                interval_seconds
            ),
        )

        self.validate_item(item)

        return item

    def validate_item(
        self,
        item: GatherItem,
    ) -> None:
        """
        驗證 GatherItem 的技能及資源
        是否存在於 Gather Database。
        """

        if not isinstance(item, GatherItem):
            raise TypeError(
                "item 必須為 GatherItem"
            )

        get_skill_definition(
            item.skill_name
        )

        get_resource_definition(
            item.skill_name,
            item.resource_name,
        )

    def validate_queue(self) -> None:
        """
        驗證 Queue 內全部項目。

        空 Queue 亦視為有效，
        由 Task 決定是否允許執行。
        """

        for item in self._settings.items:
            self.validate_item(item)

    def get_settings(
        self,
    ) -> GatherQueueSettings:
        """
        取得完整設定副本。
        """

        return GatherQueueSettings(
            items=self.get_items(),
            loop=self.loop,
        )

    def to_display_rows(
        self,
    ) -> list[dict[str, object]]:
        """
        將 Queue 轉成適合 GUI Table 顯示的資料。

        第七階段 GUI 可以直接使用。
        """

        rows: list[dict[str, object]] = []

        for index, item in enumerate(
            self._settings.items,
            start=1,
        ):
            rows.append({
                "order": index,
                "skill_name": item.skill_name,
                "resource_name": item.resource_name,
                "duration_minutes":
                    item.duration_minutes,
                "interval_seconds":
                    item.interval_seconds,
            })

        return rows

    def _validate_index(
        self,
        index: int,
    ) -> None:
        """
        驗證現有項目的 index。
        """

        if not isinstance(index, int):
            raise TypeError(
                "index 必須為 int"
            )

        if index < 0 or index >= len(
            self._settings.items
        ):
            raise IndexError(
                f"排程 index 超出範圍：{index}，"
                f"目前項目數："
                f"{len(self._settings.items)}"
            )

    def _validate_insert_index(
        self,
        index: int,
    ) -> None:
        """
        驗證插入位置。

        插入位置允許：
        0 ～目前項目數。
        """

        if not isinstance(index, int):
            raise TypeError(
                "index 必須為 int"
            )

        if index < 0 or index > len(
            self._settings.items
        ):
            raise IndexError(
                f"插入 index 超出範圍：{index}，"
                f"允許範圍："
                f"0～{len(self._settings.items)}"
            )