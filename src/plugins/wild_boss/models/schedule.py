from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone


BOSS_ACTIVE_DURATION_MINUTES = 29


@dataclass(frozen=True)
class BossDefinition:
    boss_id: str
    name: str
    list_index: int


@dataclass(frozen=True)
class BossScheduleItem:
    enabled: bool
    time_hhmm: str
    boss_id: str

    def __post_init__(self) -> None:
        try:
            datetime.strptime(self.time_hhmm, "%H:%M")
        except ValueError as error:
            raise ValueError(
                f"Invalid Hong Kong time: {self.time_hhmm}"
            ) from error

        if not self.boss_id.strip():
            raise ValueError("boss_id cannot be empty")


@dataclass
class BossScheduleSettings:
    items: list[BossScheduleItem] = field(default_factory=list)
    lead_minutes: int = 2
    retry_seconds: int = 60

    def __post_init__(self) -> None:
        if len(self.items) != 4:
            raise ValueError("Wild boss schedule must contain exactly 4 slots")
        if self.lead_minutes < 0 or self.lead_minutes > 10:
            raise ValueError("lead_minutes must be between 0 and 10")
        if self.retry_seconds < 15:
            raise ValueError("retry_seconds must be at least 15")


HONG_KONG_TIMEZONE = timezone(
    timedelta(hours=8),
    name="Asia/Hong_Kong",
)


def find_due_occurrences(
    settings: BossScheduleSettings,
    now: datetime,
    completed: set[str],
) -> list[tuple[str, BossScheduleItem, datetime]]:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    now_hk = now.astimezone(HONG_KONG_TIMEZONE)
    occurrences = []
    for slot_index, item in enumerate(settings.items):
        if not item.enabled:
            continue
        parsed_time = time.fromisoformat(item.time_hhmm)
        for day_offset in (-1, 0, 1):
            target_date = now_hk.date() + timedelta(days=day_offset)
            scheduled = datetime.combine(
                target_date,
                parsed_time,
                tzinfo=HONG_KONG_TIMEZONE,
            )
            start = scheduled - timedelta(minutes=settings.lead_minutes)
            deadline = scheduled + timedelta(
                minutes=BOSS_ACTIVE_DURATION_MINUTES
            )
            key = (
                f"{scheduled.date().isoformat()}|"
                f"{slot_index}|{item.time_hhmm}|{item.boss_id}"
            )
            if start <= now_hk < deadline and key not in completed:
                occurrences.append((key, item, scheduled))

    return sorted(occurrences, key=lambda value: value[2])
