#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from splunk_ta_gcp.common.settings import is_host_ipv6
from splunktaucclib.rest_handler.endpoint import validator
import re


class HostValidator(validator.Validator):
    def __init__(self):
        super(HostValidator, self).__init__()
        self.host_regex = re.compile(
            r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9-]*[A-Za-z0-9])$"
        )

    def validate_host(self, host: str) -> bool:
        """
        Validate whether the provided string matches the host regex.

        Args:
            host (str): Host field value

        Returns:
            bool: True if the host length is within the allowed limit, False otherwise.
        """
        return bool(self.host_regex.match(host))

    def validate_length(self, host: str) -> bool:
        """
        Validate whether the provided string does not exceed specified length.

        Args:
            host (str): Host field value

        Returns:
            bool: True if the host length is within the allowed limit, False otherwise.
        """
        if len(host) > 4096:
            self.put_msg(f"Maximum length allowed for host is 4096")
            return False
        return True

    def validate_ipv6(self, address: str) -> bool:
        """
        Validate whether the provided string is a valid IPv6 address and is enclosed within square brackets.

        Args:
            address (str): The string to be validated as an IPv6 address.

        Returns:
            bool: True if the address is a valid IPv6 address, False otherwise.
        """
        return is_host_ipv6(address)

    def validate(self, value: str, data: any) -> bool:
        """
        If the provided host value passes any one of the validation returns True
        else returns False

        Args:
            value (str): Host Field value
            data (any): Proxy configuration payload

        Returns:
            bool: Returns True if the validation succeeds False otherwise
        """
        if not self.validate_length(value):
            return False
        host_validators = [self.validate_ipv6, self.validate_host]
        is_valid_host = any(validator(value) for validator in host_validators)
        if not is_valid_host:
            self.put_msg(f"Please enter a valid hostname or IP address")
            return False
        return True
