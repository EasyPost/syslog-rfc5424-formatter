import logging
import time
import socket
import datetime
import re

version_info = (1, 0, 0)
__version__ = '.'.join(str(s) for s in version_info)
__author__ = 'EasyPost <oss@easypost.com>'


class RFC5424Formatter(logging.Formatter, object):
    '''
    A derived formatter than allows for isotime specification
    for full RFC5424 compliancy (with corrected TZ format).

    This should be combined with the Syslog Handler to actually emit logs.

    For a "proper" ISOTIME format, use "%(isotime)s" in a
    formatter instance of this class or a class derived from
    this class.  This is for a work-around where strftime
    has no mechanism to produce timezone in the format of
    "-08:00" as required by RFC5424.

    The '%(isotime)s' replacement will read in the record
    timestamp and try and reparse it.  This really is a
    problem with RFC5424 and strftime.  I am unsure if this
    will be fixed in the future (in one or the other case)

    This formatter has an added benefit of allowing for
    '%(hostname)s' to be specified which will return a '-'
    as specified in RFC5424 if socket.gethostname() returns
    bad data (exception).

    This formatter will automatically insert the RFC5424 header for you;
    the format string that you pass in the constructor is only
    applied to the message body (and should typically just be %(message)).

    The '- -' sections in the resulting message are the "msg ID" and
    "Structured-Data" Elements, respectively

    MSGID (Description from RFC5424):
       The MSGID SHOULD identify the type of message.  For example, a
   firewall might use the MSGID "TCPIN" for incoming TCP traffic and the
   MSGID "TCPOUT" for outgoing TCP traffic.  Messages with the same
   MSGID should reflect events of the same semantics.  The MSGID itself
   is a string without further semantics.  It is intended for filtering
   messages on a relay or collector.
   The NILVALUE SHOULD be used when the syslog application does not, or
   cannot, provide any value.

   Stuctured Data Example:
        [exampleSDID@32473 iut="3" eventSource="Application" eventID="1011"]
    '''
    def __init__(self, *args, **kwargs):
        self._tz_fix = re.compile(r'([+-]\d{2})(\d{2})$')
        return super(RFC5424Formatter, self).__init__(*args, **kwargs)

    def format(self, record):
        try:
            record.__dict__['hostname'] = socket.gethostname()
        except Exception:
            record.__dict__['hostname'] = '-'
        isotime = datetime.datetime.fromtimestamp(record.created).isoformat()
        tz = self._tz_fix.match(time.strftime('%z'))
        if time.timezone and tz:
            (offset_hrs, offset_min) = tz.groups()
            if int(offset_hrs) == 0 and int(offset_min) == 0:
                isotime = isotime + 'Z'
            else:
                isotime = '{0}{1}:{2}'.format(isotime, offset_hrs, offset_min)
        else:
            isotime = isotime + 'Z'

        record.__dict__['isotime'] = isotime

        header = '1 {isotime} {hostname} {name} {process} - - '.format(
            **record.__dict__
        )
        return header + super(RFC5424Formatter, self).format(record)
