import logging, os, sys
from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from typing import Literal
from contextlib import suppress
from core.event_service import EventService
from core.widgets.base import BaseWidget

from pyvda import VirtualDesktop, get_virtual_desktops
from core.validation.widgets.yasb.desktops import VALIDATION_SCHEMA

class WorkspaceButton(QPushButton):
    def __init__(self, workspace_index: int, label: str = None):
        super().__init__()
        self.workspace_index = workspace_index
        self.setProperty("class", "ws-btn")
        self.setText(label if label else str(workspace_index + 1))
        self.clicked.connect(self.activate_workspace)
        self.hide()

    def activate_workspace(self):
        try:
            VirtualDesktop(self.workspace_index + 1).go()
            pass
        except Exception:
            logging.exception(f"Failed to focus workspace at index {self.workspace_index}")


class WorkspaceWidget(BaseWidget):
    k_signal_connect = pyqtSignal(dict)
    k_signal_update = pyqtSignal(dict, dict)
    k_signal_disconnect = pyqtSignal()

    validation_schema = VALIDATION_SCHEMA

    def __init__(
            self,
            label_workspace_btn: str,
            label_default_name: str,
            label_zero_index: bool,
            hide_empty_workspaces: bool
    ):
        super().__init__(class_name="windows-desktops")

        self._event_service = EventService()
        self._label_workspace_btn = label_workspace_btn
        self._label_default_name = label_default_name
        self._label_zero_index = label_zero_index
        self._virtual_desktops = range(len(get_virtual_desktops()))
        self._prev_workspace_index = None
        self._curr_workspace_index = VirtualDesktop.current()
        self._workspace_buttons: list[WorkspaceButton] = []
        self._hide_empty_workspaces = hide_empty_workspaces

        # Disable default mouse event handling inherited from BaseWidget
        self.mousePressEvent = None

        # Construct container which holds workspace buttons
        self._workspace_container_layout: QHBoxLayout = QHBoxLayout()
        self._workspace_container_layout.setSpacing(0)
        self._workspace_container_layout.setContentsMargins(0, 0, 0, 0)
        self._workspace_container: QWidget = QWidget()
        self._workspace_container.setLayout(self._workspace_container_layout)
        self._workspace_container.setProperty("class", "windows-desktops-container")
        self._workspace_container.show()

        self.widget_layout.addWidget(self._workspace_container)

        self.timer_interval = 100
        self.register_callback("update_desktops", self._update_desktops)
        self.callback_timer = "update_desktops"
        
        self.start_timer()
    
    def _update_desktops(self):
        self._virtual_desktops = range(len(get_virtual_desktops()))

        if self._curr_workspace_index != VirtualDesktop.current().number - 1:
            self._prev_workspace_index = self._curr_workspace_index
            self._curr_workspace_index = VirtualDesktop.current().number - 1

        self._add_or_update_buttons()

    def _clear_container_layout(self):
        for i in reversed(range(self._workspace_container_layout.count())):
            old_workspace_widget = self._workspace_container_layout.itemAt(i).widget()
            self._workspace_container_layout.removeWidget(old_workspace_widget)
            old_workspace_widget.setParent(None)

    def _update_button(self, workspace_btn: WorkspaceButton) -> None:
        if self._hide_empty_workspaces:
            workspace_btn.hide()
        else:
            workspace_btn.show()
            
            if workspace_btn.workspace_index == self._curr_workspace_index:
                workspace_btn.setProperty("class", "ws-btn-focused")
                workspace_btn.setStyleSheet('')
            else:
                workspace_btn.setProperty("class", "ws-btn")
                workspace_btn.setStyleSheet('')

    def _add_or_update_buttons(self) -> None:
        buttons_added = False
        for desktop_index in self._virtual_desktops:
            try:
                button = self._workspace_buttons[desktop_index]
            except IndexError:
                button = self._try_add_workspace_button(desktop_index)
                buttons_added = True

            self._update_button(button)

        if buttons_added:
            self._workspace_buttons.sort(key=lambda btn: btn.workspace_index)
            self._clear_container_layout()

            for workspace_btn in self._workspace_buttons:
                self._workspace_container_layout.addWidget(workspace_btn)

    def _get_workspace_label(self, workspace_index):
        return str(workspace_index + 1)

    def _try_add_workspace_button(self, workspace_index: int) -> WorkspaceButton:
        workspace_button_indexes = [ws_btn.workspace_index for ws_btn in self._workspace_buttons]

        if workspace_index not in workspace_button_indexes:
            ws_label = self._get_workspace_label(workspace_index)
            workspace_btn = WorkspaceButton(workspace_index, ws_label)
            print(f'added workspace button { ws_label }')

            self._update_button(workspace_btn)
            self._workspace_buttons.append(workspace_btn)

            return workspace_btn

    def _try_remove_workspace_button(self, workspace_index: int) -> None:
        with suppress(IndexError):
            workspace_button = self._workspace_buttons[workspace_index]
            workspace_button.hide()
            print(f'Removed Workspace button { workspace_index }')
