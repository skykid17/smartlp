#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import csv


class CSVParser:
    """Class to parse CSV files and convert lines to JSON record"""

    def __init__(self, parse_csv_with_delimiter, logger):
        """Class initialization

        Args:
            parse_csv_with_delimiter: CSV delimiter
            logger: logger
        """
        self._parse_csv_with_delimiter = parse_csv_with_delimiter
        self._logger = logger

        self._headers = None
        self._truncated_line = None

    def parse_csv_line(self, csv_chunk):
        """Parses the downloaded chunk

        Args:
            csv_chunk: Downloaded chunk of the CSV file

        Yields:
            dict: yields the dict generated from CSV line with key from header and corresponding value
        """
        for line in csv_chunk:
            csv_stream = line.decode("utf-8")

            csv_line, self._truncated_line = self._handle_truncated_line(csv_stream)

            # checks if csv_stream is None because, if so, it would be a partial line,
            # and the process moves to the next line
            if not csv_line:
                continue

            parsed_line = self._parse_line(csv_line.rstrip("\r\n"))

            # if headers is not populated then, it must be the first line of the file. Extract the header.
            if not self._headers:
                self._headers = parsed_line
            else:
                # split by given delimiter parameter parse_csv_with_delimiter to get the values
                if len(parsed_line) < len(self._headers):
                    values_array += [""] * (len(self._headers) - len(values_array))
                values = {
                    self._headers[i]: parsed_line[i] for i in range(len(self._headers))
                }
                yield values

    def _parse_line(self, line):
        """Parses line based on the delimiter

        Args:
            line: CSV line to parse

        Returns:
            list: list of fields in the parsed CSV line
        """
        if not isinstance(line, str):
            return []
        if "\\t" in self._parse_csv_with_delimiter:
            r = csv.reader([line], dialect="excel-tab")
            r = list(r)
            return r.pop(0)
        else:
            r = csv.reader([line], delimiter=self._parse_csv_with_delimiter)
            return list(r)[0]

    def _handle_truncated_line(self, line):
        """Handles a truncated line. If a line is truncated partial line, it is returned to use later.

        Args:
            line: line to check whether truncated line or actual line

        Returns:
            byte_array: line - parsed line if not truncated line
            byte_array: truncated_line - truncated line
        """
        # if line does not end with a new line then it is a partial line. Save the line to use later.
        # if not line[-1] == ord("\n"):
        if not line.endswith("\n"):
            tl = self._truncated_line + line if self._truncated_line else line
            return None, tl

        # if we had a truncated line from the previous chunk, get that and prefix to the first line of current chunk.
        # reset truncated_line to None since we are done using the incomplete line.
        if self._truncated_line:
            line = self._truncated_line + line
        return line, None
