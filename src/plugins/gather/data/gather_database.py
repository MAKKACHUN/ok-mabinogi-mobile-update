from src.plugins.gather.models.GatherDefinition import (
    GatherResourceDefinition,
    GatherSkillDefinition,
)


GATHER_DATABASE: dict[str, GatherSkillDefinition] = {
    "日常採集": GatherSkillDefinition(
        name="日常採集",
        feature="daily_gathering_skill",
        resources={
            "巢穴": GatherResourceDefinition(
                name="巢穴",
                feature="nest_resource",
            ),
            "蜘蛛網": GatherResourceDefinition(
                name="蜘蛛網",
                feature="spider_web_resource",
            ),
            "水": GatherResourceDefinition(
                name="水",
                feature="water_resource",
            ),
            "水井": GatherResourceDefinition(
                name="水井",
                feature="well_resource",
            ),
            "乳牛": GatherResourceDefinition(
                name="乳牛",
                feature="dairy_cow_resource",
            ),
            "蘋果樹": GatherResourceDefinition(
                name="蘋果樹",
                feature="apple_tree_resource",
            ),
        },
    ),

    "伐木": GatherSkillDefinition(
        name="伐木",
        feature="logging_skill",
        resources={
            "樹木": GatherResourceDefinition(
                name="樹木",
                feature="tree_resource",
            ),
            "尖葉樹": GatherResourceDefinition(
                name="尖葉樹",
                feature="sharp_leaf_tree_resource",
            ),
            "粗壯樹": GatherResourceDefinition(
                name="粗壯樹",
                feature="sturdy_tree_resource",
            ),
            "成材樹": GatherResourceDefinition(
                name="成材樹",
                feature="mature_tree_resource",
            ),
            "甲胄樹": GatherResourceDefinition(
                name="甲胄樹",
                feature="armored_tree_resource",
            ),
        },
    ),

    "採礦": GatherSkillDefinition(
        name="採礦",
        feature="mining_skill",
        resources={
            "礦脈": GatherResourceDefinition(
                name="礦脈",
                feature="ore_vein_resource",
            ),
            "鐵礦脈": GatherResourceDefinition(
                name="鐵礦脈",
                feature="iron_ore_resource",
            ),
            "冰": GatherResourceDefinition(
                name="冰",
                feature="ice_resource",
            ),
            "煤炭礦脈": GatherResourceDefinition(
                name="煤炭礦脈",
                feature="coal_ore_resource",
            ),
            "銅礦脈": GatherResourceDefinition(
                name="銅礦脈",
                feature="copper_ore_item",
            ),
            "白銅礦脈": GatherResourceDefinition(
                name="白銅礦脈",
                feature="white_copper_ore_resource",
            ),
        },
    ),

    "採集藥草": GatherSkillDefinition(
        name="採集藥草",
        feature="herb_gathering_skill",
        resources={
            "藥草": GatherResourceDefinition(
                name="藥草",
                feature="herb_resource",
            ),
            "血紅藥草": GatherResourceDefinition(
                name="血紅藥草",
                feature="blood_red_herb_resource",
            ),
            "箭花": GatherResourceDefinition(
                name="箭花",
                feature="arrow_flower_resource",
            ),
            "魔力藥草": GatherResourceDefinition(
                name="魔力藥草",
                feature="magic_herb_resource",
            ),
            "新芽蘑茹": GatherResourceDefinition(
                name="新芽蘑茹",
                feature="sprout_mushroom_resource",
            ),
            "壯壯蘑茹": GatherResourceDefinition(
                name="壯壯蘑茹",
                feature="strong_mushroom_resource",
            ),
            "毅力草": GatherResourceDefinition(
                name="毅力草",
                feature="perseverance_grass_resource",
            ),
            "咻咻蘑茹": GatherResourceDefinition(
                name="咻咻蘑茹",
                feature="swift_mushroom_resource",
            ),
            "躲躲花": GatherResourceDefinition(
                name="躲躲花",
                feature="hiding_flower_resource",
            ),
            "淨淨蘑茹": GatherResourceDefinition(
                name="淨淨蘑茹",
                feature="clean_mushroom_resource",
            ),
        },
    ),

    "剪羊毛": GatherSkillDefinition(
        name="剪羊毛",
        feature="shearing_skill",
        resources={
            "羊": GatherResourceDefinition(
                name="羊",
                feature="sheep_resource",
            ),
            "捲毛羊": GatherResourceDefinition(
                name="捲毛羊",
                feature="curly_sheep_resource",
            ),
        },
    ),

    "收割": GatherSkillDefinition(
        name="收割",
        feature="harvesting_skill",
        resources={
            "小麥": GatherResourceDefinition(
                name="小麥",
                feature="wheat_resource",
            ),
            "玉米": GatherResourceDefinition(
                name="玉米",
                feature="corn_resource",
            ),
        },
    ),

    "鋤地": GatherSkillDefinition(
        name="鋤地",
        feature="hoeing_skill",
        resources={
            "馬鈴薯": GatherResourceDefinition(
                name="馬鈴薯",
                feature="potato_resource",
            ),
            "洋蔥": GatherResourceDefinition(
                name="洋蔥",
                feature="onion_resource",
            ),
            "貝類": GatherResourceDefinition(
                name="貝類",
                feature="shellfish_resource",
            ),
        },
    ),

    "昆蟲採集": GatherSkillDefinition(
        name="昆蟲採集",
        feature="insect_gathering_skill",
        resources={
            "光群": GatherResourceDefinition(
                name="光群",
                feature="light_swarm_resource",
            ),
            "雪原光群": GatherResourceDefinition(
                name="雪原光群",
                feature="snowfield_light_swarm_resource",
            ),
            "寧靜的光群": GatherResourceDefinition(
                name="寧靜的光群",
                feature="quiet_light_swarm_resource",
            ),
            "溫暖的光群": GatherResourceDefinition(
                name="溫暖的光群",
                feature="warm_light_swarm_resource",
            ),
            "冰冷的光群": GatherResourceDefinition(
                name="冰冷的光群",
                feature="cold_light_swarm_resource",
            ),
        },
    ),
}


def get_skill_definition(
    skill_name: str,
) -> GatherSkillDefinition:
    """
    根據生活技能名稱取得技能資料。

    Raises:
        ValueError:
            Database 中不存在指定技能。
    """

    skill = GATHER_DATABASE.get(skill_name)

    if skill is None:
        available_skills = "、".join(
            GATHER_DATABASE.keys()
        )

        raise ValueError(
            f"找不到生活技能：{skill_name}。"
            f"目前可用技能：{available_skills}"
        )

    return skill


def get_resource_definition(
    skill_name: str,
    resource_name: str,
) -> GatherResourceDefinition:
    """
    根據生活技能及資源名稱取得資源資料。

    Raises:
        ValueError:
            技能或資源不存在。
    """

    skill = get_skill_definition(skill_name)

    resource = skill.resources.get(resource_name)

    if resource is None:
        available_resources = "、".join(
            skill.resources.keys()
        )

        raise ValueError(
            f"生活技能「{skill_name}」中，"
            f"找不到資源「{resource_name}」。"
            f"目前可用資源：{available_resources}"
        )

    return resource


def get_skill_names() -> list[str]:
    """
    取得所有生活技能名稱。

    將來 GUI 的「生活技能」下拉選單會使用呢個函數。
    """

    return list(GATHER_DATABASE.keys())


def get_resource_names(
    skill_name: str,
) -> list[str]:
    """
    取得指定生活技能下的所有資源名稱。

    將來使用者選擇技能後，
    GUI 會利用呢個函數更新資源下拉選單。
    """

    skill = get_skill_definition(skill_name)

    return list(skill.resources.keys())


def validate_gather_database() -> None:
    """
    驗證 Gather Database 基本資料是否正確。

    程式啟動時可以呼叫，
    及早發現空名稱、空 feature 或資料 Key 不一致。
    """

    if not GATHER_DATABASE:
        raise ValueError(
            "GATHER_DATABASE 不可以為空"
        )

    for skill_key, skill in GATHER_DATABASE.items():
        if not skill_key.strip():
            raise ValueError(
                "生活技能 Key 不可以為空"
            )

        if skill_key != skill.name:
            raise ValueError(
                f"生活技能 Key 與 name 不一致："
                f"key={skill_key}，name={skill.name}"
            )

        if not skill.feature.strip():
            raise ValueError(
                f"生活技能「{skill.name}」"
                f"沒有設定 feature"
            )

        if not skill.resources:
            raise ValueError(
                f"生活技能「{skill.name}」"
                f"至少需要一個資源"
            )

        for resource_key, resource in (
            skill.resources.items()
        ):
            if not resource_key.strip():
                raise ValueError(
                    f"生活技能「{skill.name}」"
                    f"包含空白資源 Key"
                )

            if resource_key != resource.name:
                raise ValueError(
                    f"資源 Key 與 name 不一致："
                    f"key={resource_key}，"
                    f"name={resource.name}"
                )

            if not resource.feature.strip():
                raise ValueError(
                    f"資源「{resource.name}」"
                    f"沒有設定 feature"
                )