"""
Gather Plugin metadata and task registration.
"""


PLUGIN_ID = "gather"
PLUGIN_NAME = "自動採集"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = (
    "提供多生活技能採集、排程編輯、循環及 JSON 保存功能。"
)


TASK_ENTRY = [
    "src.plugins.gather.tasks.AutoGatherTask",
    "AutoGatherTask",
]


def get_task_entry() -> list[str]:
    """
    回傳可加入 config['onetime_tasks'] 的 Task Entry。
    """

    return list(TASK_ENTRY)