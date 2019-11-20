# -----------------------------------------------------------------------------
# Name:        FramTestUtil.py
# Purpose:     Python utilities for use in unit testing
#
# Author:      Jim Stearns <james.stearns@noaa.gov>
#
# Created:     4 Sep 2017
# License:     MIT
# ------------------------------------------------------------------------------

from asyncio import Queue
import logging.handlers
import unittest


class LoggingQueue(Queue):
    """ Sub-class a python queue to add syntactic sugar property to get log messages as a list of strings."""
    def __init__(self, capacity=-1):
        super().__init__(capacity)

    @property
    def messages(self):
        """ Return the message portion of each log entry as a list."""
        return [log_entry.msg for log_entry in self._queue]


class TestLoggingQueue(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger()
        self.q = LoggingQueue(-1)
        self.q_handler = logging.handlers.QueueHandler(self.q)
        self.logger.addHandler(self.q_handler)

    def test_logging_to_queue(self):
        test_msg1 = "Testing 1 2 3"
        test_msg2 = "Testing 4 5 6"

        self.logger.info(test_msg1)
        self.logger.info(test_msg2)

        self.assertEqual(2, len(self.q.messages))
        first_msg = self.q.messages[0]
        print(first_msg)
        self.assertEqual(test_msg1, first_msg)
        self.assertEqual(test_msg2, self.q.messages[1])
