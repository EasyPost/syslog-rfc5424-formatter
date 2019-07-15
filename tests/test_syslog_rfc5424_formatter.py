import logging
import logging.handlers
import tempfile
import shutil
import os
import socket
import time

from unittest import TestCase

import mock
from syslog_rfc5424_parser import SyslogMessage
from syslog_rfc5424_parser.constants import SyslogSeverity, SyslogFacility

from syslog_rfc5424_formatter import RFC5424Formatter


@mock.patch('socket.gethostname', return_value='the_host')
@mock.patch('os.getpid', return_value=1)
@mock.patch('time.time', return_value=0)
@mock.patch.dict(os.environ, {'TZ': 'UTC'})
class RFC5424FormatterTestCase(TestCase):
    def setUp(self):
        time.tzset()

    def test_basic(*args):
        f = RFC5424Formatter()
        r = logging.makeLogRecord({'name': 'root', 'msg': 'A Message'})
        assert f.format(r) == '1 1970-01-01T00:00:00Z the_host root 1 - - A Message'

    def test_non_utc(*args):
        with mock.patch.dict(os.environ, {'TZ': 'America/Phoenix'}):
            time.tzset()
            f = RFC5424Formatter()
            r = logging.makeLogRecord({'name': 'root', 'msg': 'A Message'})
            assert f.format(r) == '1 1969-12-31T17:00:00-07:00 the_host root 1 - - A Message'

    def test_long_pid(*args):
        with mock.patch('os.getpid', return_value=999999):
            f = RFC5424Formatter()
            r = logging.makeLogRecord({'name': 'root', 'msg': 'A Message'})
            assert f.format(r) == '1 1970-01-01T00:00:00Z the_host root 999999 - - A Message'

    def test_properties(*args):
        f = RFC5424Formatter()
        f.msgid = 'msgid'
        f.procid = 999999
        r = logging.makeLogRecord({'name': 'root', 'msg': 'A Message'})
        assert f.format(r) == '1 1970-01-01T00:00:00Z the_host root 999999 msgid - A Message'

    def test_properties_override(*args):
        f = RFC5424Formatter()
        f.msgid = 'msgid'
        f.procid = 999999
        r = logging.makeLogRecord({'name': 'root', 'msg': 'A Message', 'args': {'msgid': 'digsm', 'procid': 1234}})
        assert f.format(r) == '1 1970-01-01T00:00:00Z the_host root 1234 digsm - A Message'

    def test_structured_data(*args):
        f = RFC5424Formatter()
        r = logging.makeLogRecord({'name': 'root', 'msg': 'A Message', 'args': {
            'structured_data': {'name': 'value', 'sdid@32473': {'escape': '\\"]'}}
        }})
        result = f.format(r)
        assert '[sdid@32473 escape="\\\\\\"\\]"]' in result
        assert '[Undefined@32473 name="value"]' in result

    def test_format_string(*args):
        f = RFC5424Formatter('%(message)s banana')
        r = logging.makeLogRecord({'name': 'root', 'msg': 'A Message'})
        assert f.format(r) == '1 1970-01-01T00:00:00Z the_host root 1 - - A Message banana'

    def test_integration(*args):
        try:
            working_dir = tempfile.mkdtemp()
            s_path = os.path.join(working_dir, 'sock')
            s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            s.bind(s_path)
            r = logging.makeLogRecord({'name': 'root', 'msg': 'A Message', 'levelname': 'DEBUG'})
            h = logging.handlers.SysLogHandler(s_path, facility=logging.handlers.SysLogHandler.LOG_USER)
            h.setFormatter(RFC5424Formatter())
            h.handle(r)
            s.settimeout(1)
            msg_body = s.recv(1024)
            assert msg_body == b'<15>1 1970-01-01T00:00:00Z the_host root 1 - - A Message\x00'
            fields = SyslogMessage.parse(msg_body.decode('utf-8'))
            assert fields.severity == SyslogSeverity.debug
            assert fields.facility == SyslogFacility.user
            assert fields.version == 1
            assert fields.hostname == 'the_host'
            assert fields.appname == 'root'
            assert fields.msg == 'A Message\x00'
            assert fields.procid == 1
        finally:
            shutil.rmtree(working_dir)

    def test_hostname_fails(*args):
        with mock.patch('socket.gethostname', side_effect=ValueError):
            f = RFC5424Formatter()
            r = logging.makeLogRecord({'name': 'root', 'msg': 'A Message'})
            assert f.format(r) == '1 1970-01-01T00:00:00Z - root 1 - - A Message'
