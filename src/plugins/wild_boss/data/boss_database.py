from src.plugins.wild_boss.models import BossDefinition


BOSS_DATABASE: dict[str, BossDefinition] = {
    "clama": BossDefinition("clama", "克拉瑪", 2),
    "corrupted_root_beast": BossDefinition(
        "corrupted_root_beast", "腐化根獸", 1
    ),
    "peri": BossDefinition("peri", "佩里", 0),
}


def get_boss_definition(boss_id: str) -> BossDefinition:
    try:
        return BOSS_DATABASE[boss_id]
    except KeyError as error:
        raise ValueError(f"Unknown wild boss: {boss_id}") from error


def get_boss_definitions() -> list[BossDefinition]:
    return list(BOSS_DATABASE.values())
