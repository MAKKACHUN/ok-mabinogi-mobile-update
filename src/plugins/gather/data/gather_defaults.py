from src.plugins.gather.models.GatherItem import (
    GatherItem,
)
from src.plugins.gather.models.GatherQueueSettings import (
    GatherQueueSettings,
)


DEFAULT_GATHER_SETTINGS = GatherQueueSettings(
    items=[
        GatherItem(
            skill_name="採礦",
            resource_name="銅礦脈",
            duration_minutes=1,
            interval_seconds=30,
        ),
        GatherItem(
            skill_name="剪羊毛",
            resource_name="羊",
            duration_minutes=1,
            interval_seconds=30,
        ),
    ],
    loop=False,
)