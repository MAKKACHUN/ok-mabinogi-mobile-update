import time

from src.combat.CombatCheck import CombatCheck
from src.char.BaseChar import BaseChar

from ok import Logger

logger = Logger.get_logger(__name__)


class NotInCombatException(Exception):
    """未处于战斗状态异常。"""
    pass


class CharDeadException(NotInCombatException):
    """角色死亡异常。"""
    pass


class BaseCombatTask(CombatCheck):
    def __init__(self, *args, **kwargs):
        """初始化战斗任务。

        Args:
            *args: 传递给父类的参数。
            **kwargs: 传递给父类的关键字参数。
        """
        super().__init__(*args, **kwargs)
        self.char = None

    def get_ultimate_key(self):
        """获取终结技的按键。

        Returns:
            str: 终结技的按键字符串。
        """
        return self.key_config['Ultimate Key']

    def get_geniemon_key(self):
        """获取魔灵支援的按键。

        Returns:
            str: 魔灵支援的按键字符串。
        """
        return self.key_config['Geniemon Key']

    def get_combat_key(self):
        """获取战技的按键。

        Returns:
            str: 战技的按键字符串。
        """
        return self.key_config['Combat Key']

    def raise_not_in_combat(self, message, exception_type=None):
        """抛出未在战斗状态的异常。

        Args:
            message (str): 异常信息。
            exception_type (Exception, optional): 要抛出的异常类型。默认为 NotInCombatException。
        """
        logger.error(message)
        if self.reset_to_false(reason=message):
            logger.error(f'reset to false failed: {message}')
        if exception_type is None:
            exception_type = NotInCombatException
        raise exception_type(message)

    def load_char(self):
        """加载角色信息。"""
        name = None
        self.char = BaseChar(self, char_name=name)

    def combat_end(self):
        """战斗结束后的处理。"""
        self.log_info("Combat ended")

    def get_current_char(self, raise_exception=False) -> BaseChar:
        """获取当前操作的角色对象。

        Args:
            raise_exception (bool, optional): 如果找不到当前角色是否抛出异常。默认为 True。

        Returns:
            BaseChar: 当前角色对象 (`BaseChar`) 或 None。
        """
        if self.char is not None:
            return self.char
        if raise_exception and not self.in_team():
            self.raise_not_in_combat('not in_team, can not find current char!!')
        return None

    def sleep_check_combat(self, timeout, check_combat=True):
        """休眠指定时间, 并在休眠前后检查战斗状态。

        Args:
            timeout (float): 休眠的秒数。
            check_combat (bool, optional): 是否在休眠前检查战斗状态。默认为 True。
        """
        start = time.time()
        if check_combat and not self.in_combat():
            self.raise_not_in_combat('sleep check not in combat')
        self.sleep(timeout - (time.time() - start))
