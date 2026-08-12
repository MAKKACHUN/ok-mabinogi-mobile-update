from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.plugins.wild_boss.data import get_boss_definition
from src.plugins.wild_boss.models import (
    BossScheduleItem,
    BossScheduleSettings,
)


class BossScheduleStorage:
    FILE_VERSION = 1

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    def load(
        self,
        default_settings: BossScheduleSettings,
    ) -> BossScheduleSettings:
        if not self.file_path.exists():
            return self.copy_settings(default_settings)

        with self.file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Wild boss schedule JSON must be an object")
        if data.get("version") != self.FILE_VERSION:
            raise ValueError("Unsupported wild boss schedule version")

        raw_items = data.get("items")
        if not isinstance(raw_items, list):
            raise ValueError("Wild boss schedule items must be an array")

        items = []
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                raise ValueError("Wild boss schedule item must be an object")
            item = BossScheduleItem(
                enabled=self.parse_bool(raw_item.get("enabled", False)),
                time_hhmm=str(raw_item.get("time_hhmm", "")),
                boss_id=str(raw_item.get("boss_id", "")),
            )
            get_boss_definition(item.boss_id)
            items.append(item)

        return BossScheduleSettings(
            items=items,
            lead_minutes=int(data.get("lead_minutes", 2)),
            retry_seconds=int(data.get("retry_seconds", 60)),
        )

    def save(self, settings: BossScheduleSettings) -> None:
        for item in settings.items:
            get_boss_definition(item.boss_id)

        data = {
            "version": self.FILE_VERSION,
            "timezone": "Asia/Hong_Kong",
            "lead_minutes": settings.lead_minutes,
            "retry_seconds": settings.retry_seconds,
            "items": [
                {
                    "enabled": item.enabled,
                    "time_hhmm": item.time_hhmm,
                    "boss_id": item.boss_id,
                }
                for item in settings.items
            ],
        }
        self.atomic_write(data)

    def atomic_write(self, data: dict[str, Any]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.file_path.with_suffix(
            self.file_path.suffix + ".tmp"
        )
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        temporary_path.replace(self.file_path)

    @staticmethod
    def copy_settings(
        settings: BossScheduleSettings,
    ) -> BossScheduleSettings:
        return BossScheduleSettings(
            items=list(settings.items),
            lead_minutes=settings.lead_minutes,
            retry_seconds=settings.retry_seconds,
        )

    @staticmethod
    def parse_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "on"}
        return bool(value)


class BossRuntimeStorage:
    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    def load_completed(self) -> set[str]:
        if not self.file_path.exists():
            return set()
        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            values = data.get("completed", [])
            return {str(value) for value in values}
        except Exception:
            return set()

    def save_completed(self, completed: set[str]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        values = sorted(completed)[-32:]
        temporary_path = self.file_path.with_suffix(".json.tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump({"completed": values}, file, indent=2)
        temporary_path.replace(self.file_path)
