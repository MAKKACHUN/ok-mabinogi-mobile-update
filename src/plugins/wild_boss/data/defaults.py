from src.plugins.wild_boss.models import (
    BossScheduleItem,
    BossScheduleSettings,
)


DEFAULT_BOSS_SCHEDULE = BossScheduleSettings(
    items=[
        BossScheduleItem(False, "00:00", "clama"),
        BossScheduleItem(False, "06:00", "clama"),
        BossScheduleItem(False, "12:00", "clama"),
        BossScheduleItem(False, "18:00", "clama"),
    ],
    lead_minutes=5,
    retry_seconds=60,
)
