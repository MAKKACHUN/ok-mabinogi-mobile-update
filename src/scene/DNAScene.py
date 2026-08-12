from ok import Logger, BaseScene

logger = Logger.get_logger(__name__)


class DNAScene(BaseScene):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._in_team = None

    def reset(self):
        self._in_team = None

    def in_team(self, fun):
        if self._in_team is None:
            self._in_team = fun()
        return self._in_team
