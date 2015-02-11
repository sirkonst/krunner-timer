# -*- coding: utf-8 -*-t
# ------------------------------------------------------------------------------
from __future__ import unicode_literals, absolute_import

from PyKDE4 import plasmascript
from PyKDE4.plasma import Plasma
from PyKDE4.kdeui import KIcon
from PyQt4.QtCore import QTimer

from datetime import datetime

from .notifications import Notifications
# ------------------------------------------------------------------------------


class _Runable(object):

    def start(self, link_fn):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def isActive(self):
        raise NotImplementedError

# ------------------------------------------------------------------------------


class Timer(_Runable):
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


class Alarm(_Runable):
    """
    :param str comment: user comment for timer
    :param int hour:
    :param int minute:
    """

    def __init__(self, parse_str):
        if ' ' in parse_str:
            v, c = parse_str.split(' ', 1)
        else:
            v, c = parse_str, ''

        h, m = v.split(':')
        h, m = int(h), int(m)
        if not (0 <= h < 24):
            raise ValueError
        if not (0 <= m < 60):
            raise ValueError

        self.hour = h
        self.minute = m
        self.comment = c
        self._timer = None

    def start(self, link_fn):
        self._timer = QTimer()
        self._timer.timeout.connect(lambda: link_fn(self))

        now = datetime.now()
        a = datetime(
            year=now.year, month=now.month,
            day=self.hour < now.hour and now.day + 1 or now.day,
            hour=self.hour, minute=self.minute, tzinfo=now.tzinfo
        )
        d = a - now
        if d.total_seconds() > 1:
            self._timer.start(d.total_seconds() * 1000)

    def stop(self):
        self._timer.stop()

    def isActive(self):
        return self._timer and self._timer.isActive()

# ------------------------------------------------------------------------------


class AlarmTimerRunner(plasmascript.Runner):

    def init(self):
        self.addSyntax(
            Plasma.RunnerSyntax('timer :q:', 'Set timer :q:')
        )
        self.timer_list = []
        self.alarm_list = []
        self.notifications = Notifications(
            'krunner-alarmtimer',
            source='{base}/contents/misc/notifyrc'.format(
                base=self.package().path()
            )
        )

    def _timer(self, context):
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
            m.setSubtext('select to cancel')
            m.setType(Plasma.QueryMatch.ExactMatch)
            m.setIcon(KIcon('chronometer'))
            m.setRelevance(0.6)
            m.setData(timer)

            context.addMatch(q, m)

    def _alarm(self, context):
        q = context.query()
        if not (
            q == 'alarm' or q.startsWith('alarm ')
        ):
            return

        m = Plasma.QueryMatch(self.runner)
        m.setText(
            'Set alarm example: "15:00 watch TV news".'
        )
        m.setSubtext('')
        m.setType(Plasma.QueryMatch.ExactMatch)
        m.setIcon(KIcon('chronometer'))
        m.setRelevance(1)
        m.setData(q)

        try:
            _s = unicode(q.toUtf8(), encoding="UTF-8")
            _s = _s[len('alarm'):].strip()

            alarm = Alarm(_s)

            if alarm.comment:
                _t = 'Set alarm on {}:{:0>2} for: "{}"'
            else:
                _t = 'Set alarm on {}:{:0>2}'
            m.setText(
                _t.format(alarm.hour, alarm.minute, alarm.comment)
            )
            m.setData(alarm)

            context.addMatch(q, m)
        except ValueError:
            context.addMatch(q, m)

         # active timers
        for alarm in self.alarm_list:
            m = Plasma.QueryMatch(self.runner)
            _t = 'Active alarm on {}:{:0>2}'
            if alarm.comment:
                _t = 'Active alarm on {}:{:0>2}: "{}"'
            m.setText(
                _t.format(
                    alarm.hour, alarm.minute, alarm.comment
                )
            )
            m.setSubtext('select to cancel')
            m.setType(Plasma.QueryMatch.ExactMatch)
            m.setIcon(KIcon('chronometer'))
            m.setRelevance(0.6)
            m.setData(alarm)

            context.addMatch(q, m)

    def match(self, context):
        if not context.isValid():
            return

        self._timer(context)
        self._alarm(context)

    def run(self, context, match):
        obj = match.data().toPyObject()

        if isinstance(obj, Timer):
            if not obj.isActive():
                obj.start(self.on_timer)
                self.timer_list.append(obj)

                comment = obj.comment
                _t = 'For {val} {suff}.'
                if comment:
                    _t = 'For {val} {suff}: "{comm}".'
                body = _t.format(
                    val=obj.orig_value, suff=obj.suffix, comm=comment)
                self.notifications.notify(
                    'start-timer', 'Timer has been running', body
                )
            else:
                obj.stop()
                self.timer_list.remove(obj)
        elif isinstance(obj, Alarm):
            if not obj.isActive():
                obj.start(self.on_alarm)
                self.alarm_list.append(obj)

                comment = obj.comment
                _t = 'On {}:{:0>2}.'
                if comment:
                    _t = 'On {}:{:0>2}: "{}".'
                body = _t.format(
                    obj.hour, obj.minute, obj.comment)
                self.notifications.notify(
                    'set-alarm', 'Alarm is set', body
                )
            else:
                obj.stop()
                self.alarm_list.remove(obj)

    def on_timer(self, timer):
        timer.stop()
        self.timer_list.remove(timer)

        comment = timer.comment
        _t = 'On {val} {suff}.'
        if comment:
            _t = 'On {val} {suff}: "{comm}".'
        body = _t.format(val=timer.orig_value, suff=timer.suffix, comm=comment)

        self.notifications.notify(
            'on-timer', 'Timer alarm!', body, timeout=120
        )

    def on_alarm(self, alarm):
        alarm.stop()
        self.alarm_list.remove(alarm)

        _t = '{}:{:0>2}.'
        if alarm.comment:
            _t = '{}:{:0>2}: "{}".'
        body = _t.format(
            alarm.hour, alarm.minute, alarm.comment)

        self.notifications.notify(
            'on-alarm', 'Alarm now!', body, timeout=120
        )

# ------------------------------------------------------------------------------


def CreateRunner(parent):
    return AlarmTimerRunner(parent)