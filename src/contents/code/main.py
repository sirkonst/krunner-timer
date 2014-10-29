# -*- coding: utf-8 -*-t
# ------------------------------------------------------------------------------
from __future__ import unicode_literals, absolute_import

from PyKDE4 import plasmascript
from PyKDE4.plasma import Plasma
from PyKDE4.kdeui import KIcon
from PyQt4.QtCore import QTimer

import dbus

from .notifications import Notifications
# ------------------------------------------------------------------------------


def notify(title, body='', app_name='', app_icon='', timeout=30,
           actions=None, hints=None, replaces_id=0):
        _bus_name = 'org.freedesktop.Notifications'
        _object_path = '/org/freedesktop/Notifications'
        _interface_name = _bus_name

        session_bus = dbus.SessionBus()
        obj = session_bus.get_object(_bus_name, _object_path)
        interface = dbus.Interface(obj, _interface_name)
        interface.Notify(
            app_name, replaces_id, app_icon, title, body, actions or [],
            hints or [], timeout * 1000
        )

# ------------------------------------------------------------------------------


class Timer(object):
    """
    :param str comment: user comment for timer
    :param int seconds:
    :param str suffix: time value suffix: seconds, minutes, hours
    :param int orig_value:
    """

    def __init__(self, parse_str):
        """
        :param str parse_str:
        :raise ValueError: if can't parse string
        """
        data = parse_str.split(" ", 1)
        if len(data) == 2:
            self.comment = data[1]
        else:
            self.comment = ""

        value = data[0]  # like 15m, 5s, 1h

        self.orig_value = int(value[:-1])  # integer value (raise ValueError)
        s = value[-1].lower()  # time suffix: s, m, h

        if s == 's':
            self.suffix = 'seconds'
            self.seconds = self.orig_value
        elif s == 'm':
            self.suffix = 'minutes'
            self.seconds = self.orig_value * 60
        elif s == 'h':
            self.suffix = 'hours'
            self.seconds = self.orig_value * 60 * 60
        else:
            raise ValueError

        self._timer = None

    def start(self, link_fn):
        self._timer = QTimer()
        self._timer.timeout.connect(lambda: link_fn(self))
        self._timer.start(self.seconds * 1000)

    def stop(self):
        self._timer.stop()

    def isActive(self):
        return self._timer and self._timer.isActive()

# ------------------------------------------------------------------------------


class TimerRunner(plasmascript.Runner):

    def init(self):
        self.addSyntax(
            Plasma.RunnerSyntax('timer :q:[s:m:h]', 'Set timer :q:')
        )
        self.timer_list = []
        self.notifications = Notifications(
            'krunner-timer',
            source='{base}/contents/misc/notifyrc'.format(
                base=self.package().path()
            )
        )

    def match(self, context):
        if not context.isValid():
            return

        q = context.query()

        if not (
            q == 'timer' or q.startsWith('timer ')
        ):
            return

        m = Plasma.QueryMatch(self.runner)
        m.setText(
            'Set timer example: "5m feed the cat".'

        )
        m.setSubtext(
            'You can use suffix s, m, h for seconds, minutes and hours.'
        )
        m.setType(Plasma.QueryMatch.ExactMatch)
        m.setIcon(KIcon('chronometer'))
        m.setRelevance(1)
        m.setData(q)

        try:
            _s = unicode(q.toUtf8(), encoding="UTF-8")
            timer = Timer(_s[len('timer'):].strip())

            _t = 'Set timer for {val} {suf}.'
            if timer.comment:
                _t = 'Set timer for {val} {suf}: "{com}".'
            m.setText(_t.format(
                val=timer.orig_value, suf=timer.suffix, com=timer.comment
            ))
            m.setData(timer)

            context.addMatch(q, m)
        except ValueError:
            context.addMatch(q, m)

        # active timers
        for timer in self.timer_list:
            m = Plasma.QueryMatch(self.runner)
            _t = 'Running timer: {val} {suf}'
            if timer.comment:
                _t = 'Running timer: {val} {suf} "{com}"'
            m.setText(
                _t.format(
                    val=timer.orig_value, suf=timer.suffix, com=timer.comment
                )
            )
            m.setSubtext('select for cancel')
            m.setType(Plasma.QueryMatch.ExactMatch)
            m.setIcon(KIcon('chronometer'))
            m.setRelevance(0.9)
            m.setData(timer)

            context.addMatch(q, m)

    def run(self, context, match):
        timer = match.data().toPyObject()
        if not isinstance(timer, Timer):
            return

        if not timer.isActive():
            timer.start(self.on_timer)
            self.timer_list.append(timer)

            comment = timer.comment
            _t = 'For {val} {suff}.'
            if comment:
                _t = 'For {val} {suff}: "{comm}".'
            body = _t.format(
                val=timer.orig_value, suff=timer.suffix, comm=comment)
            self.notifications.notify(
                'start-timer', 'Timer is running', body
            )
        else:
            timer.stop()
            self.timer_list.remove(timer)

    def on_timer(self, timer):
        timer.stop()
        self.timer_list.remove(timer)

        comment = timer.comment
        _t = 'On {val} {suff}.'
        if comment:
            _t = 'On {val} {suff}: "{comm}".'
        body = _t.format(val=timer.orig_value, suff=timer.suffix, comm=comment)

        self.notifications.notify(
            'on-timer', 'Timer alarm!', body
        )

# ------------------------------------------------------------------------------


def CreateRunner(parent):
    return TimerRunner(parent)