import csv
import os
import sys
from splunksdc import log as logging

logger = logging.get_module_logger()


class FSLock:
    @classmethod
    def _create_runtime(cls):
        if os.name == 'nt':
            import msvcrt   # pylint: disable=import-error

            def lock(fd):
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1024)

            def unlock(fd):
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1024)

            return lock, unlock
        else:
            import fcntl

            def lock(fd):
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            def unlock(fd):
                fcntl.flock(fd, fcntl.LOCK_UN)

        return lock, unlock

    @classmethod
    def open(cls, path):
        lock, unlock = cls._create_runtime()
        flag = os.O_RDWR | os.O_CREAT | os.O_TRUNC
        fd = os.open(path, flag)
        return cls(fd, lock, unlock)

    def __init__(self, fd, lock, unlock):
        self._fd = fd
        self._lock = lock
        self._unlock = unlock

    def acquire(self):
        self._lock(self._fd)

    def release(self):
        self._unlock(self._fd)

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class LogExceptions:

    _debugging = True if 'pydevd' in sys.modules else False

    def __init__(self, logger, message, epilogue=None, types=Exception):
        self._logger = logger
        self._message = message
        self._epilogue = epilogue
        self._types = types

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except self._types as e:
                self._logger.exception(self._message)
                if self._epilogue:
                    return self._epilogue(e)
                raise e
        return wrapper if not self._debugging else func


class LogWith:
    def __init__(self, **kwargs):
        self._pairs = list(kwargs.items())

    def __call__(self, func):
        pairs = self._pairs

        def wrapper(*args, **kwargs):
            ctx = dict()
            for key, value in pairs:
                if isinstance(value, property):
                    value = value.fget(args[0])
                ctx[key] = value
            with logging.LogContext(**ctx):
                return func(*args, **kwargs)
        return wrapper


def parseLine(line, parse_csv_with_delimiter):
    """Parses a csv line, via the chosen delimiter, using the built-in csv parser to respect escapes etc.
    Args:
        @param: line
        @paramType: string
        @param: parse_csv_with_delimiter
        @paramType: string
    Returns:
        list: fields as a list
    """
    if not isinstance(line, str):
        return []
    if "\\t" in parse_csv_with_delimiter:
        r = csv.reader([line], dialect='excel-tab')
        r = list(r)
        return r.pop(0)
    else:
        if "\\s" in parse_csv_with_delimiter:
            parse_csv_with_delimiter = " "
        r = csv.reader([line], delimiter=parse_csv_with_delimiter)
        return list(r)[0]


def parseCSVLine(line, headers, parse_csv_with_delimiter):
    """ Parse each line into CSV format via the chosen delimiter. If line is a header, split into list and hold.
    Else, map header values to subsequent row values. Return values and headers.
    @param: line
    @paramType: string
    @param: headers
    @paramType: list
    @param: parse_csv_with_delimiter
    @paramType: string
    """
    # remove carriage return and new line characters from the end of the line, and parse the line by the delimiter
    values_array = parseLine(line.rstrip("\r\n"), parse_csv_with_delimiter)
    values = None

    # if fieldnames is not populated then, it must be the first line of the file. Extract the header.
    if not headers:
        headers = values_array
        logger.debug(
            "Extracted Header: {}".format(
                headers
            ), headers_count=len(headers)
        )
    else:
        # split by given delimiter parameter parse_csv_with_delimiter to get the values
        if len(values_array) < len(headers):
            values_array += [""] * (
                    len(headers) - len(values_array)
            )
        values = {
            headers[i]: values_array[i]
            for i in range(len(headers))
        }

    return values, headers


def handle_truncated_line(line, truncated_line):
    """ Handles a truncated line. If a line is truncated partial line, it is returned to use later.
    @param: line
    @paramType: byte_array
    @param: truncated_line
    @paramType: byte_array
    """
    # if line does not end with a new line then it is a partial line. Save the line to use later.
    if not line[-1] == ord("\n"):
        logger.debug("Truncated Line: ", truncated_line=line)
        return None, line

    # if we had a truncated line from the previous chunk, get that and prefix to the first line of current chunk.
    # reset truncated_line to None since we are done using the incomplete line.
    if truncated_line:
        logger.debug("Prefix previous truncated line: ", completed_event=truncated_line + line)
        line = truncated_line + line
    return line, None
