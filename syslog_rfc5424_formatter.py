import logging
import time
import socket
import datetime
import re

version_info = (1, 2, 2)
__version__ = '.'.join(str(s) for s in version_info)
__author__ = 'EasyPost <oss@easypost.com>'


class RFC5424FormatterError(Exception):
    pass


class InvalidSDIDError(RFC5424FormatterError):
    pass


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

    Stuctured Data Example:

        [exampleSDID@32473 iut="3" eventSource="Application" eventID="1011"]

    To use structured data:

       1. Construct the logger with an sd_id kwarg (or set the `sd_id` attribute on the logger object)
       2. Construct your individual records with `{'args': {'structured_data': {'iut': '3'}}}`
    '''
    def __init__(self, fmt='%(message)s', datefmt=None, style='%', procid=None, msgid=None, sd_id=None):
        # note: we accept and throw away "style" because our stuff only works with %
        # we also accept and throw away datefmt for similar reasons
        self._tz_fix = re.compile(r'([+-]\d{2})(\d{2})$')
        self._procid = procid
        self._msgid = msgid
        self._sd_id = sd_id
        return super(RFC5424Formatter, self).__init__(fmt=fmt, datefmt=None)

    @property
    def procid(self):
        """Default PROCID to add to syslog message"""
        return self._procid

    @procid.setter
    def procid(self, id):
        self._procid = id

    @property
    def msgid(self):
        """Default MSGID to add to syslog message"""
        return self._msgid

    @msgid.setter
    def msgid(self, id):
        self._msgid = id

    @property
    def sd_id(self):
        """Default SD-ID to add to STRUCTURED-DATA section in syslog message"""
        return self._sd_id

    @sd_id.setter
    def sd_id(self, sd_id):
        if not sd_id:
            raise InvalidSDIDError('SD-ID cannot be empty')
        self._sd_id = sd_id

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
        record.__dict__['procid'] = self.procid if self.procid else record.process
        record.__dict__['msgid'] = self.msgid if self.msgid else '-'

        if 'structured_data' in record.args:
            if not isinstance(record.args['structured_data'], dict):
                raise ValueError('structured_data must be a dict')

            all_sddata = {}
            default_sdparam = {}

            for key, value in record.args['structured_data'].items():
                if isinstance(value, dict):
                    all_sddata[key] = value
                else:
                    default_sdparam[key] = value

            if len(default_sdparam) > 0:
                if self.sd_id in all_sddata:
                    raise InvalidSDIDError('Cannot use same SD-ID twice')
                if not self.sd_id:
                    raise InvalidSDIDError('SD-ID cannot be empty')
                all_sddata[self.sd_id] = default_sdparam

            sd = ''
            for sdid, data in all_sddata.items():
                sd += '[{0}'.format(sdid)
                for key, value in data.items():
                    escaped = str(value).replace('\\', '\\\\').replace(']', '\\]').\
                        replace('"', '\\"')
                    sd += ' {0}="{1}"'.format(key, escaped)
                sd += ']'

            record.__dict__['sd'] = sd
        else:
            record.__dict__['sd'] = '-'

        for key in ('procid', 'msgid'):
            if key in record.args:
                record.__dict__[key] = record.args.pop(key)

        header = '1 {isotime} {hostname} {name} {procid} {msgid} {sd} '.format(
            **record.__dict__
        )
        return header + super(RFC5424Formatter, self).format(record)
