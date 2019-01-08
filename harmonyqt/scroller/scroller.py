# Copyright 2018 miruka
# This file is part of harmonyqt, licensed under GPLv3.

from PyQt5.QtWidgets import QWidget


class Scroller:
    def __init__(self, widget: QWidget) -> None:
        self.widget = widget
        self.hbar   = widget.horizontalScrollBar()
        self.vbar   = widget.verticalScrollBar()


    @property
    def hmin(self) -> int:
        return self.hbar.minimum()

    @property
    def vmin(self) -> int:
        return self.vbar.minimum()

    @property
    def h(self) -> int:
        return self.hbar.value()

    @property
    def v(self) -> int:
        return self.vbar.value()

    @property
    def hmax(self) -> int:
        return self.hbar.maximum()

    @property
    def vmax(self) -> int:
        return self.vbar.maximum()


    @property
    def hstep(self) -> int:
        return self.hbar.singleStep()

    @property
    def vstep(self) -> int:
        return self.vbar.singleStep()

    @property
    def hstep_page(self) -> int:
        return self.hbar.pageStep()

    @property
    def vstep_page(self) -> int:
        return self.vbar.pageStep()


    def hset(self, to: int) -> "Scroller":
        self.hbar.setValue(to)
        return self

    def vset(self, to: int) -> "Scroller":
        self.vbar.setValue(to)
        return self


    def go_left(self, times: int = 1) -> "Scroller":
        return self.hset(self.h - self.hstep * times)

    def go_right(self, times: int = 1) -> "Scroller":
        return self.hset(self.h + self.hstep * times)

    def go_up(self, times: int = 1) -> "Scroller":
        return self.vset(self.v - self.vstep * times)

    def go_down(self, times: int = 1) -> "Scroller":
        return self.vset(self.v + self.vstep * times)


    def go_page_left(self, times: int = 1) -> "Scroller":
        return self.hset(self.h - self.hstep_page * times)

    def go_page_right(self, times: int = 1) -> "Scroller":
        return self.hset(self.h + self.hstep_page * times)

    def go_page_up(self, times: int = 1) -> "Scroller":
        return self.vset(self.v - self.vstep_page * times)

    def go_page_down(self, times: int = 1) -> "Scroller":
        return self.vset(self.v + self.vstep_page * times)


    def go_min_left(self) -> "Scroller":
        return self.hset(self.hmin)

    def go_max_right(self) -> "Scroller":
        return self.hset(self.hmax)

    def go_top(self) -> "Scroller":
        return self.vset(self.vmin)

    def go_bottom(self) -> "Scroller":
        return self.vset(self.vmax)
