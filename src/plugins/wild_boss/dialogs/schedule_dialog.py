from __future__ import annotations

from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from src.plugins.wild_boss.data import get_boss_definitions
from src.plugins.wild_boss.models import (
    BossScheduleItem,
    BossScheduleSettings,
)


class BossScheduleDialog(QDialog):
    COLUMN_SLOT = 0
    COLUMN_ENABLED = 1
    COLUMN_TIME = 2
    COLUMN_BOSS = 3

    def __init__(
        self,
        settings: BossScheduleSettings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("野外首領排程（香港時間）")
        self.setModal(True)
        self.resize(680, 430)
        self._result: BossScheduleSettings | None = None
        self._build_ui(settings)

    def _build_ui(self, settings: BossScheduleSettings) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("每日野外首領排程")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        description = QLabel(
            "時間一律使用香港時間（UTC+8）。"
            "程式會在指定時間前數分鐘前往所選首領。"
        )
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        self.table = QTableWidget(4, 4, self)
        self.table.setHorizontalHeaderLabels(
            ["時段", "啟用", "香港時間", "野外首領"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            self.COLUMN_SLOT, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            self.COLUMN_ENABLED, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            self.COLUMN_TIME, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            self.COLUMN_BOSS, QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setVisible(False)

        bosses = get_boss_definitions()
        for row, item in enumerate(settings.items):
            slot = QTableWidgetItem(str(row + 1))
            slot.setFlags(
                slot.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            self.table.setItem(row, self.COLUMN_SLOT, slot)

            enabled = QCheckBox()
            enabled.setChecked(item.enabled)
            self.table.setCellWidget(row, self.COLUMN_ENABLED, enabled)

            time_edit = QTimeEdit()
            time_edit.setDisplayFormat("HH:mm")
            time_edit.setTime(QTime.fromString(item.time_hhmm, "HH:mm"))
            self.table.setCellWidget(row, self.COLUMN_TIME, time_edit)

            boss_combo = QComboBox()
            for boss in bosses:
                boss_combo.addItem(boss.name, boss.boss_id)
            index = boss_combo.findData(item.boss_id)
            boss_combo.setCurrentIndex(max(0, index))
            self.table.setCellWidget(row, self.COLUMN_BOSS, boss_combo)

        layout.addWidget(self.table)

        form = QFormLayout()
        self.lead_spin = QSpinBox()
        self.lead_spin.setRange(0, 10)
        self.lead_spin.setSuffix(" 分鐘")
        self.lead_spin.setValue(settings.lead_minutes)
        form.addRow("提前前往：", self.lead_spin)

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(15, 300)
        self.retry_spin.setSuffix(" 秒")
        self.retry_spin.setValue(settings.retry_seconds)
        form.addRow("未開放時重試：", self.retry_spin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        try:
            items = []
            for row in range(4):
                enabled = self.table.cellWidget(row, self.COLUMN_ENABLED)
                time_edit = self.table.cellWidget(row, self.COLUMN_TIME)
                boss_combo = self.table.cellWidget(row, self.COLUMN_BOSS)
                if not isinstance(enabled, QCheckBox):
                    raise TypeError("Missing enabled checkbox")
                if not isinstance(time_edit, QTimeEdit):
                    raise TypeError("Missing time editor")
                if not isinstance(boss_combo, QComboBox):
                    raise TypeError("Missing boss selector")
                items.append(
                    BossScheduleItem(
                        enabled=enabled.isChecked(),
                        time_hhmm=time_edit.time().toString("HH:mm"),
                        boss_id=str(boss_combo.currentData()),
                    )
                )

            self._result = BossScheduleSettings(
                items=items,
                lead_minutes=self.lead_spin.value(),
                retry_seconds=self.retry_spin.value(),
            )
        except Exception as error:
            QMessageBox.warning(self, "排程設定無效", str(error))
            return
        super().accept()

    def get_settings(self) -> BossScheduleSettings:
        if self._result is None:
            raise RuntimeError("Schedule has not been saved")
        return self._result
