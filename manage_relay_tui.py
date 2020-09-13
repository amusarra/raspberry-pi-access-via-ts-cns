#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This Python script manage_relay_tui.py implements a relay activation and deactivation
mechanism through the TUI (Text-based User Interface).

MIT License

Raspberry Pi - Access via Smart Card TS-CNS

Copyright (c) 2020 Antonio Musarra's Blog - https://www.dontesta.it

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in the
Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

__author__ = "Antonio Musarra"
__copyright__ = "Copyright 2020 Antonio Musarra's Blog"
__credits__ = ["Antonio Musarra"]
__version__ = "1.0.0"
__license__ = "MIT"
__maintainer__ = "Antonio Musarra"
__email__ = "antonio.musarra@gmail.com"
__status__ = "Development"

import datetime
import logging
from asyncio import Future, ensure_future
from io import StringIO

import RPi.GPIO as GPIO
import emoji
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pid.decorator import pidfile
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout import HSplit, VSplit, Layout, D, Float, FloatContainer, VerticalAlign, HorizontalAlign, \
    Window, FormattedTextControl, WindowAlign
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Box, Button, Frame, Label, TextArea, Dialog

# Definition and emoji creation for messages to the user.
# For more emoji https://www.webfx.com/tools/emoji-cheat-sheet/
em_bulb = emoji.emojize(':bulb:', use_aliases=True)
em_status_changed = emoji.emojize(':thumbsup:', use_aliases=True)
em_status_on = emoji.emojize(':red_circle:', use_aliases=True)
em_status_off = emoji.emojize(':black_circle:', use_aliases=True)

# Dictionary of relationship between relay identification and BCM pin
dict_relay_bcm = {
    1: 23,
    2: 24,
    3: 25,
    4: 16
}

# Scheduler Object
scheduler = BackgroundScheduler()

logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(funcName)s :: %(lineno)d \
:: %(message)s', level=logging.DEBUG, filename='manage_relay_tui.log')

logging.getLogger('apscheduler').setLevel(logging.INFO)


class MessageDialog:
    def __init__(self, title, text):
        self.future = Future()

        def set_done():
            self.future.set_result(None)

        ok_button = Button(text="OK", handler=(lambda: set_done()))

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text=text)]),
            buttons=[ok_button],
            width=D(preferred=80),
            modal=True,
        )

    def __pt_container__(self):
        return self.dialog


class TextInputDialog:
    def __init__(self, title="", label_text="", completer=None):
        self.future = Future()

        def accept_text(buf):
            get_app().layout.focus(ok_button)
            buf.complete_state = None
            return True

        def accept():
            self.future.set_result(self.text_area.text)

        def cancel():
            self.future.set_result(None)

        self.text_area = TextArea(
            completer=completer,
            history=cron_expression_history(),
            multiline=False,
            width=D(preferred=40),
            accept_handler=accept_text,
            style="class:text-area-dialog"
        )

        ok_button = Button(text="OK", handler=accept)
        cancel_button = Button(text="Cancel", handler=cancel)

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text=label_text), self.text_area]),
            buttons=[ok_button, cancel_button],
            width=D(preferred=80),
            modal=True
        )

    def __pt_container__(self):
        return self.dialog


async def show_dialog_as_float(dialog):
    """ Coroutine. """
    float_ = Float(content=dialog)
    root_container.floats.insert(0, float_)

    app = get_app()

    focused_before = app.layout.current_window
    app.layout.focus(dialog)
    result = await dialog.future
    app.layout.focus(focused_before)

    if float_ in root_container.floats:
        root_container.floats.remove(float_)

    return result


# Event handlers for all the buttons.
def action_relay(relay_id, show_notification=True, append=False):
    if GPIO.input(dict_relay_bcm[relay_id]):
        activate_relay(relay_id, show_notification, append)
    else:
        de_activate_relay(relay_id, show_notification, append)


# Get relay status
def action_relay_status():
    relay_status_string = []

    for relay_id, bcm_value in dict_relay_bcm.items():
        if GPIO.input(bcm_value):
            relay_status_string.append(f'Status of the RelayId {relay_id:d}  {em_status_off}\n')
        else:
            relay_status_string.append(f'Status of the RelayId {relay_id:d}  {em_status_on}\n')

    text_area.text = "".join(relay_status_string)


# Activate the relay
def activate_relay(relay_id, show_notification=True, append=False):
    if 1 <= relay_id <= 4:
        GPIO.output(dict_relay_bcm[relay_id], GPIO.LOW)

        if show_notification:
            show_notification_activity_relays(f"Activate Relay with id {str(relay_id)}  {em_status_changed}\n", append)


# CleanUp the resources
def cleanup():
    GPIO.cleanup()


# De-Activate the relay
def de_activate_relay(relay_id, show_notification=True, append=False):
    if 1 <= relay_id <= 4:
        GPIO.output(dict_relay_bcm[relay_id], GPIO.HIGH)

        if show_notification:
            show_notification_activity_relays(f"Deactivate Relay with id {str(relay_id)}  {em_status_changed}\n",
                                              append)


def cron_expression_history():
    history = InMemoryHistory()
    history.append_string("1;*/1 * * * *")
    history.append_string("2;*/1 * * * *")
    history.append_string("3;*/1 * * * *")
    history.append_string("4;*/1 * * * *")

    return history


# Exit from Application
def exit_app(event):
    scheduler_shutdown()
    cleanup()
    get_app().exit()


# Info box
def info_box():
    text_area.text = "This simple program is useful for activating or deactivating the relays of\n" \
                     "the board composed of four relays and connected to the Raspberry Pi. " \
                     "\n\n" \
                     "For the wiring diagram, refer to the article " \
                     "Un primo maggio 2020 a base di Raspberry Pi, Bot Telegram, Display LCD e Relè " \
                     "https://bit.ly/UnPrimoMaggio2020ABaseDiRaspberryPiBotTelegramDisplayLCDRele or the article " \
                     "Raspberry Pi – Un esempio di applicazione della TS-CNS " \
                     "https://bit.ly/3hkJ8Aj" \
                     "\n\n" \
                     "The source code is available " \
                     "on GitHub https://github.com/amusarra/raspberry-pi-access-via-ts-cns"


# Initialize the GPIO for the relay module
def initialize_relay():
    GPIO.setmode(GPIO.BCM)
    for relay_id, bcm_value in dict_relay_bcm.items():
        GPIO.setup(bcm_value, GPIO.OUT, initial=GPIO.HIGH)


def scheduler_add_job(schedule_settings):
    if schedule_settings is not None:
        schedule_settings_detail = schedule_settings.split(";")

        logging.info(f'Schedule Settings: {schedule_settings}')

        relay_id = int(schedule_settings_detail[0])
        crontab_expression = schedule_settings_detail[1]

        if 1 <= relay_id <= 4:
            job_id = f"job_relay_{relay_id}"

            logging.info(f'Relay Id: {relay_id}')
            logging.info(f'Cron Expression: {crontab_expression} for Relay Id: {relay_id}')

            job = scheduler.get_job(job_id=job_id)

            if job is not None:
                scheduler.reschedule_job(job_id=job_id,
                                         trigger=CronTrigger.from_crontab(crontab_expression, 'UTC'))
                logging.info(f'Job with the name {job_id} already exits then rescheduling')
            else:
                scheduler.add_job(lambda: action_relay(relay_id, append=True),
                                  CronTrigger.from_crontab(crontab_expression, 'UTC'),
                                  name=job_id, id=job_id)

            if not scheduler.running:
                logging.info('Starting Scheduler...')
                scheduler.start()

                logging.info('Scheduler Started')

            application.invalidate()
        else:
            raise ValueError('The value of Relay Id must be between 1 and 4')


# Scheduler Shutdown
def scheduler_shutdown(show_notification=False):
    if scheduler.running:
        scheduler.shutdown(wait=False)

        logging.info('Scheduler Shutdown')

        if show_notification:
            show_message("Scheduler", "Executed scheduler shutdown")


def show_message(title, text):
    async def coroutine():
        dialog = MessageDialog(title, text)
        await show_dialog_as_float(dialog)

    ensure_future(coroutine())


def show_notification_activity_relays(message, append=False):
    if append:
        old_message_notification = text_area.text
        current_message = f'{datetime.datetime.utcnow().isoformat()} - {message}'
        relay_status_string = [old_message_notification, current_message]

        text_area.text = "".join(relay_status_string)
    else:
        text_area.text = message


def open_dialog_schedule_relay():
    async def coroutine():
        open_dialog = TextInputDialog(
            title="Set the schedule for the relay",
            label_text="Enter the relay id and crontab expression (es: 1;*/5 * * * *):"
        )

        schedule_settings = await show_dialog_as_float(open_dialog)

        try:
            scheduler_add_job(schedule_settings)
        except Exception as ex:
            logging.error(ex)
            show_message("Errors occurred", "{}".format(ex))

    ensure_future(coroutine())


def view_scheduled_jobs():
    jobs = StringIO()

    scheduler.print_jobs(out=jobs)
    text_area.text = f"The jobs list:\n\n{jobs.getvalue()}"


# Key bindings.
kb = KeyBindings()
kb.add("tab")(focus_next)
kb.add("s-tab")(focus_previous)
kb.add("c-q")(exit_app)

# All the widgets for the UI.
button_relay_1 = Button("Activate/Deactivate Relay 1", handler=lambda: action_relay(1))
button_relay_2 = Button("Activate/Deactivate Relay 2", handler=lambda: action_relay(2))
button_relay_3 = Button("Activate/Deactivate Relay 3", handler=lambda: action_relay(3))
button_relay_4 = Button("Activate/Deactivate Relay 4", handler=lambda: action_relay(4))
button_relay_scheduling = Button("Schedule Relay", handler=lambda: open_dialog_schedule_relay())
button_relay_view_scheduled_jobs = Button("View Scheduled Jobs", handler=lambda: view_scheduled_jobs())
button_relay_scheduling_shutdown = Button("Shutdown Scheduler",
                                          handler=lambda: scheduler_shutdown(show_notification=True))
button_relay_status = Button("Relay Status", handler=lambda: action_relay_status())
button_info = Button("Info", handler=lambda: info_box())
button_exit = Button("Exit", handler=lambda: exit_app(event=False))
text_area = TextArea(height=30, focusable=True, focus_on_click=True, read_only=True,
                     scrollbar=True, dont_extend_height=True, dont_extend_width=True)

# Combine all the widgets in a UI.
# The `FloatContainer` which can contain another container for the background, as well as a list of floating
# containers on top of it.
root_container = FloatContainer(
    floats=[
        # Top float.
        Float(
            Window(width=120, height=1, align=WindowAlign.RIGHT,
                   content=FormattedTextControl(text="[Tab or Shift+Tab to move the focus] [CTRL+Q Exit]"),
                   style="class:top-header"
                   ),
            top=0,
        ),
        # Bottom float.
        Float(
            Window(width=120, height=1, align=WindowAlign.CENTER,
                   content=FormattedTextControl(
                       text="Antonio Musarra's Blog 2009 - 2020 (c) - https://www.dontesta.it | "
                            "https://github.com/amusarra"), style="class:bottom-header"
                   ),
            bottom=0
        ),
    ],
    content=HSplit(
        [
            VSplit(
                [
                    Box(
                        body=HSplit([button_relay_1, button_relay_2, button_relay_3,
                                     button_relay_4, button_relay_scheduling, button_relay_view_scheduled_jobs,
                                     button_relay_scheduling_shutdown, button_relay_status, button_info, button_exit],
                                    padding=1, width=40),
                        padding=0,
                        style="class:left-pane",
                    ),
                    Box(body=Frame(text_area), padding=0, style="class:right-pane", width=80),
                ],
                align=HorizontalAlign.CENTER
            )
        ],
        align=VerticalAlign.CENTER
    ),
)

layout = Layout(container=root_container, focused_element=button_relay_1)

# Styling.
style = Style(
    [
        ("left-pane", "bg:#3D349A"),
        ("right-pane", "bg:#954801"),
        ("button", "#ffffff"),
        ("button-arrow", "#000000"),
        ("button focused", "bg:#ff0000"),
        ("text-area focused", "bg:#954801"),
        ("bottom-header", "reverse"),
        ("top-header", "reverse"),
        ("dialog.body", "bg:#034f27"),
        ("dialog frame.label", "bg:#034f27 #ffffff"),
        ("text-area-dialog", "bg:#2b41bd #ffffff"),
    ]
)


# Build a main application object.
application = Application(layout=layout, key_bindings=kb, style=style,
                          full_screen=True, after_render=info_box(), mouse_support=True)


@pidfile()
def main():
    initialize_relay()
    application.run()


if __name__ == "__main__":
    main()
