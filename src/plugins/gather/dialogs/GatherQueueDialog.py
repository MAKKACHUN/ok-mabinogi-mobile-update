from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.plugins.gather.data.gather_database import (
    get_resource_names,
    get_skill_names,
)
from src.plugins.gather.managers.GatherQueueManager import (
    GatherQueueManager,
)
from src.plugins.gather.models.GatherItem import (
    GatherItem,
)
from src.plugins.gather.models.GatherQueueSettings import (
    GatherQueueSettings,
)


class GatherQueueDialog(QDialog):
    """
    採集排程編輯視窗。

    功能：
    ・新增採集項目
    ・刪除採集項目
    ・上移／下移
    ・選擇生活技能
    ・根據生活技能動態更新資源選項
    ・設定執行分鐘
    ・設定每輪間隔秒數
    ・設定是否循環執行
    ・驗證並輸出 GatherQueueSettings
    """

    COLUMN_ORDER = 0
    COLUMN_SKILL = 1
    COLUMN_RESOURCE = 2
    COLUMN_DURATION = 3
    COLUMN_INTERVAL = 4

    DEFAULT_DURATION_MINUTES = 25.0
    DEFAULT_INTERVAL_SECONDS = 90

    MIN_DURATION_MINUTES = 0.1
    MAX_DURATION_MINUTES = 1440.0

    MIN_INTERVAL_SECONDS = 1
    MAX_INTERVAL_SECONDS = 3600

    def __init__(
        self,
        settings: Optional[GatherQueueSettings] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("自動採集排程設定")
        self.setModal(True)
        self.resize(900, 560)

        self._result_settings: Optional[
            GatherQueueSettings
        ] = None

        self._initial_settings = self._copy_settings(
            settings
        )

        self._build_ui()
        self._load_settings(
            self._initial_settings
        )

    @staticmethod
    def _copy_settings(
        settings: Optional[GatherQueueSettings],
    ) -> GatherQueueSettings:
        """
        建立設定副本，避免 Dialog 編輯期間
        直接改動外部設定。
        """

        if settings is None:
            return GatherQueueSettings(
                items=[],
                loop=False,
            )

        return GatherQueueSettings(
            items=list(settings.items),
            loop=bool(settings.loop),
        )

    def _build_ui(self) -> None:
        """
        建立 Dialog UI。
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )
        main_layout.setSpacing(12)

        title_label = QLabel(
            "自動採集排程"
        )
        title_label.setStyleSheet(
            "font-size: 20px; "
            "font-weight: bold;"
        )

        description_label = QLabel(
            "排程會按照表格由上至下執行。"
            "生活技能改變後，資源選單會自動更新。"
        )
        description_label.setWordWrap(True)

        main_layout.addWidget(
            title_label
        )
        main_layout.addWidget(
            description_label
        )

        self.table = QTableWidget(
            0,
            5,
            self,
        )

        self.table.setHorizontalHeaderLabels([
            "順序",
            "生活技能",
            "資源",
            "執行時間（分鐘）",
            "每輪間隔（秒）",
        ])

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            self.COLUMN_ORDER,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            self.COLUMN_SKILL,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            self.COLUMN_RESOURCE,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            self.COLUMN_DURATION,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            self.COLUMN_INTERVAL,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        main_layout.addWidget(
            self.table,
            stretch=1,
        )

        operation_layout = QHBoxLayout()

        self.add_button = QPushButton(
            "新增"
        )
        self.remove_button = QPushButton(
            "刪除"
        )
        self.move_up_button = QPushButton(
            "上移"
        )
        self.move_down_button = QPushButton(
            "下移"
        )

        operation_layout.addWidget(
            self.add_button
        )
        operation_layout.addWidget(
            self.remove_button
        )
        operation_layout.addWidget(
            self.move_up_button
        )
        operation_layout.addWidget(
            self.move_down_button
        )
        operation_layout.addStretch(1)

        self.loop_checkbox = QCheckBox(
            "全部排程完成後循環執行"
        )

        operation_layout.addWidget(
            self.loop_checkbox
        )

        main_layout.addLayout(
            operation_layout
        )

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        save_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Save
        )
        cancel_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Cancel
        )

        if save_button is not None:
            save_button.setText(
                "保存"
            )

        if cancel_button is not None:
            cancel_button.setText(
                "取消"
            )

        main_layout.addWidget(
            self.button_box
        )

        self.add_button.clicked.connect(
            self.add_row
        )
        self.remove_button.clicked.connect(
            self.remove_selected_row
        )
        self.move_up_button.clicked.connect(
            self.move_selected_row_up
        )
        self.move_down_button.clicked.connect(
            self.move_selected_row_down
        )

        self.button_box.accepted.connect(
            self.accept
        )
        self.button_box.rejected.connect(
            self.reject
        )

    def _load_settings(
        self,
        settings: GatherQueueSettings,
    ) -> None:
        """
        將 GatherQueueSettings 載入表格。
        """

        self.table.setRowCount(0)

        for item in settings.items:
            self.add_row(
                item=item,
            )

        self.loop_checkbox.setChecked(
            settings.loop
        )

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def add_row(
        self,
        checked: bool = False,
        item: Optional[GatherItem] = None,
    ) -> None:
        """
        新增一行採集排程。

        checked 參數係 Qt clicked signal 傳入，
        呢度唔需要使用。
        """

        del checked

        skill_names = get_skill_names()

        if not skill_names:
            QMessageBox.warning(
                self,
                "無法新增",
                "Gather Database 沒有任何生活技能。",
            )
            return

        if item is None:
            skill_name = skill_names[0]

            resource_names = get_resource_names(
                skill_name
            )

            if not resource_names:
                QMessageBox.warning(
                    self,
                    "無法新增",
                    f"生活技能「{skill_name}」"
                    f"沒有任何資源。",
                )
                return

            resource_name = resource_names[0]
            duration_minutes = (
                self.DEFAULT_DURATION_MINUTES
            )
            interval_seconds = (
                self.DEFAULT_INTERVAL_SECONDS
            )

        else:
            skill_name = item.skill_name
            resource_name = item.resource_name
            duration_minutes = (
                item.duration_minutes
            )
            interval_seconds = int(
                item.interval_seconds
            )

        row = self.table.rowCount()

        self.table.insertRow(
            row
        )

        order_item = QTableWidgetItem(
            str(row + 1)
        )
        order_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.table.setItem(
            row,
            self.COLUMN_ORDER,
            order_item,
        )

        skill_combo = self._create_skill_combo(
            row=row,
            selected_skill=skill_name,
        )

        resource_combo = (
            self._create_resource_combo(
                row=row,
                skill_name=skill_name,
                selected_resource=resource_name,
            )
        )

        duration_spin = (
            self._create_duration_spin(
                row=row,
                value=duration_minutes,
            )
        )

        interval_spin = (
            self._create_interval_spin(
                row=row,
                value=interval_seconds,
            )
        )

        self.table.setCellWidget(
            row,
            self.COLUMN_SKILL,
            skill_combo,
        )
        self.table.setCellWidget(
            row,
            self.COLUMN_RESOURCE,
            resource_combo,
        )
        self.table.setCellWidget(
            row,
            self.COLUMN_DURATION,
            duration_spin,
        )
        self.table.setCellWidget(
            row,
            self.COLUMN_INTERVAL,
            interval_spin,
        )

        self.table.selectRow(
            row
        )

        self._refresh_order_numbers()

    def _create_skill_combo(
        self,
        row: int,
        selected_skill: str,
    ) -> QComboBox:
        """
        建立生活技能下拉選單。
        """

        combo = QComboBox(
            self.table
        )

        skill_names = get_skill_names()

        combo.addItems(
            skill_names
        )

        if selected_skill in skill_names:
            combo.setCurrentText(
                selected_skill
            )
        elif skill_names:
            combo.setCurrentIndex(0)

        combo.currentTextChanged.connect(
            lambda skill_name, widget=combo:
                self._on_skill_changed(
                    widget,
                    skill_name,
                )
        )

        combo.activated.connect(
            lambda _index, target_row=row:
                self.table.selectRow(
                    target_row
                )
        )

        return combo

    def _create_resource_combo(
        self,
        row: int,
        skill_name: str,
        selected_resource: str,
    ) -> QComboBox:
        """
        建立資源下拉選單。

        選項只會包含指定生活技能的資源。
        """

        combo = QComboBox(
            self.table
        )

        resource_names = get_resource_names(
            skill_name
        )

        combo.addItems(
            resource_names
        )

        if selected_resource in resource_names:
            combo.setCurrentText(
                selected_resource
            )
        elif resource_names:
            combo.setCurrentIndex(0)

        combo.activated.connect(
            lambda _index, target_row=row:
                self.table.selectRow(
                    target_row
                )
        )

        return combo

    def _create_duration_spin(
        self,
        row: int,
        value: float,
    ) -> QDoubleSpinBox:
        """
        建立執行時間輸入欄位。
        """

        spin = QDoubleSpinBox(
            self.table
        )

        spin.setRange(
            self.MIN_DURATION_MINUTES,
            self.MAX_DURATION_MINUTES,
        )
        spin.setDecimals(1)
        spin.setSingleStep(1.0)
        spin.setSuffix(" 分")
        spin.setValue(
            float(value)
        )

        spin.valueChanged.connect(
            lambda _value, target_row=row:
                self.table.selectRow(
                    target_row
                )
        )

        return spin

    def _create_interval_spin(
        self,
        row: int,
        value: int,
    ) -> QSpinBox:
        """
        建立每輪間隔輸入欄位。
        """

        spin = QSpinBox(
            self.table
        )

        spin.setRange(
            self.MIN_INTERVAL_SECONDS,
            self.MAX_INTERVAL_SECONDS,
        )
        spin.setSingleStep(1)
        spin.setSuffix(" 秒")
        spin.setValue(
            int(value)
        )

        spin.valueChanged.connect(
            lambda _value, target_row=row:
                self.table.selectRow(
                    target_row
                )
        )

        return spin

    def _on_skill_changed(
        self,
        skill_combo: QComboBox,
        skill_name: str,
    ) -> None:
        """
        生活技能改變後，
        即時更新同一行資源下拉選單。
        """

        row = self._find_widget_row(
            skill_combo
        )

        if row < 0:
            return

        self.table.selectRow(
            row
        )

        resource_combo = self.table.cellWidget(
            row,
            self.COLUMN_RESOURCE,
        )

        if not isinstance(
            resource_combo,
            QComboBox,
        ):
            return

        resource_names = get_resource_names(
            skill_name
        )

        old_resource = (
            resource_combo.currentText()
        )

        resource_combo.blockSignals(True)

        try:
            resource_combo.clear()
            resource_combo.addItems(
                resource_names
            )

            if old_resource in resource_names:
                resource_combo.setCurrentText(
                    old_resource
                )
            elif resource_names:
                resource_combo.setCurrentIndex(0)

        finally:
            resource_combo.blockSignals(False)

    def _find_widget_row(
        self,
        target_widget: QWidget,
    ) -> int:
        """
        根據 Cell Widget 尋找所在行。
        """

        for row in range(
            self.table.rowCount()
        ):
            for column in range(
                self.table.columnCount()
            ):
                widget = self.table.cellWidget(
                    row,
                    column,
                )

                if widget is target_widget:
                    return row

        return -1

    def _get_selected_row(self) -> int:
        """
        取得目前選中行。
        """

        selected_rows = (
            self.table.selectionModel()
            .selectedRows()
        )

        if selected_rows:
            return selected_rows[0].row()

        current_row = self.table.currentRow()

        if current_row >= 0:
            return current_row

        return -1

    def remove_selected_row(self) -> None:
        """
        刪除目前選中行。
        """

        row = self._get_selected_row()

        if row < 0:
            QMessageBox.information(
                self,
                "刪除排程",
                "請先選擇要刪除的排程。",
            )
            return

        self.table.removeRow(
            row
        )

        self._refresh_order_numbers()
        self._reconnect_row_selection_handlers()

        remaining_rows = (
            self.table.rowCount()
        )

        if remaining_rows > 0:
            new_row = min(
                row,
                remaining_rows - 1,
            )
            self.table.selectRow(
                new_row
            )

    def move_selected_row_up(self) -> None:
        """
        將目前排程向上移一格。
        """

        row = self._get_selected_row()

        if row < 0:
            QMessageBox.information(
                self,
                "上移排程",
                "請先選擇要移動的排程。",
            )
            return

        if row == 0:
            return

        rows = self._read_rows_without_validation()

        rows[row - 1], rows[row] = (
            rows[row],
            rows[row - 1],
        )

        self._reload_rows(
            rows=rows,
            selected_row=row - 1,
        )

    def move_selected_row_down(self) -> None:
        """
        將目前排程向下移一格。
        """

        row = self._get_selected_row()

        if row < 0:
            QMessageBox.information(
                self,
                "下移排程",
                "請先選擇要移動的排程。",
            )
            return

        last_row = (
            self.table.rowCount() - 1
        )

        if row >= last_row:
            return

        rows = self._read_rows_without_validation()

        rows[row], rows[row + 1] = (
            rows[row + 1],
            rows[row],
        )

        self._reload_rows(
            rows=rows,
            selected_row=row + 1,
        )

    def _reload_rows(
        self,
        rows: list[GatherItem],
        selected_row: int,
    ) -> None:
        """
        用指定項目重新建立表格。
        """

        self.table.setRowCount(0)

        for item in rows:
            self.add_row(
                item=item,
            )

        if (
            self.table.rowCount() > 0
            and 0 <= selected_row
            < self.table.rowCount()
        ):
            self.table.selectRow(
                selected_row
            )

    def _refresh_order_numbers(self) -> None:
        """
        更新第一欄順序號碼。
        """

        for row in range(
            self.table.rowCount()
        ):
            item = self.table.item(
                row,
                self.COLUMN_ORDER,
            )

            if item is None:
                item = QTableWidgetItem()
                self.table.setItem(
                    row,
                    self.COLUMN_ORDER,
                    item,
                )

            item.setText(
                str(row + 1)
            )
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

    def _reconnect_row_selection_handlers(
        self,
    ) -> None:
        """
        刪除行後，重新建立表格，
        確保各 Widget 的 row 索引正確。

        直接重新載入目前資料，
        可以避免 lambda 保留舊 row。
        """

        if self.table.rowCount() <= 0:
            return

        selected_row = max(
            0,
            self._get_selected_row(),
        )

        rows = self._read_rows_without_validation()

        self._reload_rows(
            rows=rows,
            selected_row=min(
                selected_row,
                len(rows) - 1,
            ),
        )

    def _read_rows_without_validation(
        self,
    ) -> list[GatherItem]:
        """
        將表格內容轉成 GatherItem。

        此方法主要供上移、下移及重建表格使用。
        Database 配搭會由 GatherItem／Manager
        在保存時再完整驗證。
        """

        items: list[GatherItem] = []

        for row in range(
            self.table.rowCount()
        ):
            skill_combo = self.table.cellWidget(
                row,
                self.COLUMN_SKILL,
            )
            resource_combo = self.table.cellWidget(
                row,
                self.COLUMN_RESOURCE,
            )
            duration_spin = self.table.cellWidget(
                row,
                self.COLUMN_DURATION,
            )
            interval_spin = self.table.cellWidget(
                row,
                self.COLUMN_INTERVAL,
            )

            if not isinstance(
                skill_combo,
                QComboBox,
            ):
                continue

            if not isinstance(
                resource_combo,
                QComboBox,
            ):
                continue

            if not isinstance(
                duration_spin,
                QDoubleSpinBox,
            ):
                continue

            if not isinstance(
                interval_spin,
                QSpinBox,
            ):
                continue

            items.append(
                GatherItem(
                    skill_name=(
                        skill_combo.currentText()
                    ),
                    resource_name=(
                        resource_combo.currentText()
                    ),
                    duration_minutes=(
                        duration_spin.value()
                    ),
                    interval_seconds=float(
                        interval_spin.value()
                    ),
                )
            )

        return items

    def _build_validated_settings(
        self,
    ) -> GatherQueueSettings:
        """
        驗證表格內容並建立最終設定。
        """

        items = (
            self._read_rows_without_validation()
        )

        queue_manager = GatherQueueManager(
            initial_items=items,
            loop=self.loop_checkbox.isChecked(),
        )

        queue_manager.validate_queue()

        return queue_manager.get_settings()

    def accept(self) -> None:
        """
        按保存時驗證設定。
        """

        try:
            settings = (
                self._build_validated_settings()
            )

        except Exception as error:
            QMessageBox.warning(
                self,
                "排程設定無效",
                str(error),
            )
            return

        self._result_settings = settings

        super().accept()

    def get_settings(
        self,
    ) -> GatherQueueSettings:
        """
        取得保存後的排程設定。

        必須在 Dialog Accepted 後呼叫。
        """

        if self._result_settings is None:
            raise RuntimeError(
                "排程尚未保存"
            )

        return self._copy_settings(
            self._result_settings
        )