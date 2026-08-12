from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.plugins.gather.managers.GatherQueueManager import (
    GatherQueueManager,
)
from src.plugins.gather.models.GatherItem import (
    GatherItem,
)
from src.plugins.gather.models.GatherQueueSettings import (
    GatherQueueSettings,
)


class GatherQueueStorage:
    """
    採集排程 JSON 儲存器。

    負責：
    ・將 GatherQueueSettings 保存成 JSON
    ・由 JSON 載入 GatherQueueSettings
    ・驗證載入資料
    ・JSON 不存在時回傳預設設定
    """

    FILE_VERSION = 1

    def __init__(
        self,
        file_path: str | Path,
    ) -> None:
        self.file_path = Path(file_path)

    def save(
        self,
        settings: GatherQueueSettings,
    ) -> None:
        """
        將採集排程保存到 JSON。
        """

        queue_manager = GatherQueueManager(
            initial_items=settings.items,
            loop=settings.loop,
        )
        queue_manager.validate_queue()

        data = {
            "version": self.FILE_VERSION,
            "loop": settings.loop,
            "items": [
                {
                    "skill_name": item.skill_name,
                    "resource_name": item.resource_name,
                    "duration_minutes":
                        item.duration_minutes,
                    "interval_seconds":
                        item.interval_seconds,
                }
                for item in settings.items
            ],
        }

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = self.file_path.with_suffix(
            self.file_path.suffix + ".tmp"
        )

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        temporary_path.replace(
            self.file_path
        )

    def load(
        self,
        default_settings: GatherQueueSettings,
    ) -> GatherQueueSettings:
        """
        從 JSON 載入排程。

        JSON 不存在時回傳 default_settings 副本。
        """

        if not self.file_path.exists():
            return self._copy_settings(
                default_settings
            )

        try:
            with self.file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            return self._parse_data(data)

        except Exception as error:
            raise RuntimeError(
                f"載入採集排程失敗："
                f"{self.file_path}。"
                f"原因：{error}"
            ) from error

    def _parse_data(
        self,
        data: Any,
    ) -> GatherQueueSettings:
        """
        將 JSON object 轉成 GatherQueueSettings。
        """

        if not isinstance(data, dict):
            raise ValueError(
                "JSON 最外層必須為 object"
            )

        version = data.get("version")

        if version != self.FILE_VERSION:
            raise ValueError(
                f"不支援的排程版本：{version}"
            )

        loop = self._parse_bool(
            data.get(
                "loop",
                False,
            )
        )

        raw_items = data.get(
            "items",
            [],
        )

        if not isinstance(raw_items, list):
            raise ValueError(
                "items 必須為 array"
            )

        items: list[GatherItem] = []

        for index, raw_item in enumerate(
            raw_items,
            start=1,
        ):
            if not isinstance(
                raw_item,
                dict,
            ):
                raise ValueError(
                    f"第 {index} 個排程項目"
                    f"必須為 object"
                )

            item = GatherItem(
                skill_name=str(
                    raw_item.get(
                        "skill_name",
                        "",
                    )
                ).strip(),
                resource_name=str(
                    raw_item.get(
                        "resource_name",
                        "",
                    )
                ).strip(),
                duration_minutes=float(
                    raw_item.get(
                        "duration_minutes",
                        0,
                    )
                ),
                interval_seconds=float(
                    raw_item.get(
                        "interval_seconds",
                        0,
                    )
                ),
            )

            items.append(item)

        queue_manager = GatherQueueManager(
            initial_items=items,
            loop=loop,
        )
        queue_manager.validate_queue()

        return queue_manager.get_settings()

    @staticmethod
    def _parse_bool(
        value: Any,
    ) -> bool:
        """
        安全解析 JSON 布林值。
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
            }:
                return True

            if normalized in {
                "false",
                "0",
                "no",
                "off",
                "",
            }:
                return False

        return bool(value)

    @staticmethod
    def _copy_settings(
        settings: GatherQueueSettings,
    ) -> GatherQueueSettings:
        return GatherQueueSettings(
            items=list(settings.items),
            loop=bool(settings.loop),
        )