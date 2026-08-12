from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class GatherResourceDefinition:
    """
    一個可採集資源的固定資料。

    name:
        遊戲畫面及 GUI 顯示名稱，例如「銅礦脈」。

    feature:
        圖片辨識 Template 名稱，例如「copper_ore_item」。
    """

    name: str
    feature: str


@dataclass(frozen=True)
class GatherSkillDefinition:
    """
    一個生活技能的固定資料。

    name:
        遊戲畫面及 GUI 顯示名稱，例如「採礦」。

    feature:
        生活技能頁面的 Template 名稱，例如「mining_skill」。

    resources:
        此生活技能可選擇的資源。
        Key 為資源名稱，Value 為 GatherResourceDefinition。
    """

    name: str
    feature: str
    resources: Mapping[str, GatherResourceDefinition]