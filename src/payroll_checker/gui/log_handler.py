"""A logging handler that forwards records into the GUI's message queue."""

import logging
import queue


class QueueLogHandler(logging.Handler):
    """Push formatted log records onto a `queue.Queue` for a tkinter poller to drain.

    Attached in addition to (not instead of) the usual rotating file
    handler from `logging_setup.configure_logging`, so anything already
    logged today (e.g. `runner.run_check`'s `logger.exception` on a failed
    check) shows up in both the log file and the GUI's log pane.
    """

    def __init__(self, message_queue: "queue.Queue") -> None:
        super().__init__()
        self.message_queue = message_queue

    def emit(self, record: logging.LogRecord) -> None:
        self.message_queue.put(("log", self.format(record), record.levelname))
