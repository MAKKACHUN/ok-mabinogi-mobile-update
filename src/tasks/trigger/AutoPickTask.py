import time

from qfluentwidgets import FluentIcon

from ok import Logger
from ok import TriggerTask
from src.scene.DNAScene import DNAScene
from src.tasks.BaseDNATask import BaseDNATask, f_black_color

logger = Logger.get_logger(__name__)


class AutoPickTask(TriggerTask, BaseDNATask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Auto Pick"
        self.description = "Auto Pick in Game World"
        self.icon = FluentIcon.SHOPPING_CART
        self.scene: DNAScene | None = None

    def send_fs(self):
        self.send_key(self.get_interact_key())
        self.sleep(0.2)

    def run(self):
        if not self.scene.in_team(self.in_team_and_world):
            return
        start = time.time()
        while time.time() - start < 1:
            f = self.find_best_match_in_box(self.f_search_box, ["pick_up_f", "pick_up_e"], threshold=0.8)
            if not f:
                return
            percent = self.calculate_color_percentage(f_black_color, f)
            if percent < 0.5:
                self.log_debug(f'f black color percent: {percent} wait')
                self.next_frame()
                continue
            dialog_search = f.copy(x_offset=f.width * 2.75, width_offset=f.width, height_offset=f.height,
                                   y_offset=-f.height * 0.5,
                                   name='search_dialog')
            dialog_hand = self.find_feature('dialog_hand', box=dialog_search,
                                            threshold=0.6)

            if dialog_hand:
                self.send_fs()
                return True
            self.next_frame()
