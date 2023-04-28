from __future__ import annotations

from itertools import zip_longest
from typing import Optional

from rich.console import RenderableType
from rich.text import TextType
from textual.app import ComposeResult
from textual.events import Event
from textual.widgets import (
    Button,
    LoadingIndicator, RadioButton, TabbedContent, TabPane, ContentSwitcher, Tabs
)
from textual.widgets._tabbed_content import ContentTab

from mys_goods_tool.custom_css import *


class RadioStatus(RadioButton, can_focus=False):
    """
    完成的进度节点，不允许点击交互
    可通过触发事件以即时修改value属性
    """

    class ChangeStatus(Event):
        """
        请求按钮状态修改的事件
        """

        def __init__(self, radio_status: RadioStatus):
            self.radio_status = radio_status
            super().__init__()

    class TurnOn(ChangeStatus):
        """请求按钮状态修改为亮起的事件"""
        pass

    class TurnOff(ChangeStatus):
        """请求按钮状态修改为熄灭的事件"""
        pass

    def turn_on(self):
        """修改按钮状态为亮起"""
        self.post_message(RadioStatus.TurnOn(self))

    def turn_off(self):
        """修改按钮状态为熄灭"""
        self.post_message(RadioStatus.TurnOff(self))

    def toggle(self) -> None:
        """
        重写按钮交互，交互时不会改变按钮状态
        """
        pass


class StaticStatus(Static):
    """
    实时文本说明，可通过触发事件以即时修改文本属性
    """

    class ChangeRenderable(Event):
        """
        请求renderable属性（此处与文本相关）修改的事件
        """

        def __init__(self, static_status: StaticStatus, renderable: RenderableType, text_align: Optional[str] = None):
            self.static_status = static_status
            self.renderable = renderable
            self.text_align = text_align
            super().__init__()

    def change_text(self, renderable: RenderableType, text_align: Optional[str] = None) -> None:
        """修改renderable属性（此处与文本相关）"""
        self.post_message(StaticStatus.ChangeRenderable(self, renderable, text_align))


class ControllableButton(Button):
    """
    带隐藏、显示、禁用、启用控制方法的按钮
    """

    def show(self):
        """
        显示
        """
        self.display = BLOCK

    def hide(self):
        """
        隐藏
        """
        self.display = NONE

    def disable(self):
        """
        禁用
        """
        self.disabled: bool = True

    def enable(self):
        """
        启用
        """
        self.disabled: bool = False


class LoadingDisplay(LoadingIndicator):
    def show(self):
        """
        显示
        """
        self.display = BLOCK

    def hide(self):
        """
        隐藏
        """
        self.display = NONE


class DynamicTabbedContent(TabbedContent):
    def __init__(self, *titles: TextType):
        super().__init__(*titles)
        self.tabs: Optional[Tabs] = None
        self.content_switcher: Optional[ContentSwitcher] = None

    @classmethod
    def _set_id(cls, content: TabPane, new_id: str) -> TabPane:
        """Set an id on the content, if not already present.

        Args:
            content: a TabPane.
            new_id: New `is` attribute, if it is not already set.

        Returns:
            The same TabPane.
        """
        if content.id is None:
            content.id = new_id
        return content

    @property
    def contents(self):
        """返回所有TabPane"""
        yield from self._tab_content

    def append(self, content: TabPane):
        """增加TabPane"""
        self.titles.append(content._title)
        self._tab_content.append(content)
        tab_pane_with_id = self._set_id(content, f"tab-{len(self.content_switcher.children) + 1}")
        content_tab = ContentTab(tab_pane_with_id._title, tab_pane_with_id.id or "")
        mount_await = self.content_switcher.mount(tab_pane_with_id)
        self.call_after_refresh(mount_await)
        self.tabs.add_tab(content_tab)

    def compose(self) -> ComposeResult:
        """Compose the tabbed content."""

        # Wrap content in a `TabPane` if required.
        pane_content = [
            (
                self._set_id(content, f"tab-{index}")
                if isinstance(content, TabPane)
                else TabPane(
                    title or self.render_str(f"Tab {index}"), content, id=f"tab-{index}"
                )
            )
            for index, (title, content) in enumerate(
                zip_longest(self.titles, self._tab_content), 1
            )
        ]
        # Get a tab for each pane
        tabs = [
            ContentTab(content._title, content.id or "") for content in pane_content
        ]
        # Yield the tabs
        self.tabs = Tabs(*tabs, active=self._initial or None)
        yield self.tabs
        # Yield the content switcher and panes
        self.content_switcher = ContentSwitcher(initial=self._initial or None)
        with self.content_switcher:
            yield from pane_content
