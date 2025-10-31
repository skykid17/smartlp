#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
from datetime import datetime, timedelta
from splunktaucclib.rest_handler.endpoint import validator
import ipaddress
import re

REPORT_CONTENT_TYPES = [
    "Office365GroupsActivityDetail",
    "OneDriveUsageAccountDetail",
    "SharePointSiteUsageDetail",
    "TeamsUserActivityUserDetail",
    "YammerGroupsActivityDetail",
]


class UTCDateValidator(validator.Validator):
    def __init__(self):
        super(UTCDateValidator, self).__init__()

    def validate(self, value, data):
        try:
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            return True
        except ValueError:
            self.put_msg("Valid Datetime format is 'YYYY-MM-DDTHH:MM:SS'")
            return False


class GraphAPIStartDateValidator(validator.Validator):
    def __init__(self):
        super(GraphAPIStartDateValidator, self).__init__()

    def validate(self, payload):
        # Validate the Date format
        if payload.get("content_type") in REPORT_CONTENT_TYPES:
            if not payload.get("start_date"):
                payload.update(
                    {
                        "start_date": (datetime.utcnow() - timedelta(days=7)).strftime(
                            "%Y-%m-%d"
                        )
                    }
                )
                return True, ""
            else:
                try:
                    start_date = datetime.strptime(
                        payload["start_date"], "%Y-%m-%d"
                    ).date()
                    utc_now = datetime.utcnow().date()
                    if start_date > utc_now:
                        return False, "Start Date cannot be in the future."
                    if (utc_now - start_date).days >= 28:
                        return (
                            False,
                            "Start date cannot be older than 28 days in the past.",
                        )
                    return True, ""
                except ValueError:
                    return False, "Valid Start Date format is 'YYYY-MM-DD'"
        else:
            return True, ""


class GraphAPIAuditLogsDelayThrottleDateValidator(validator.Validator):
    def __init__(self):
        super(GraphAPIAuditLogsDelayThrottleDateValidator, self).__init__()

    def validate(self, payload):
        # Validate Start & End Date based on the Delay Throttle
        delay_throttle_min = payload.get("delay_throttle_min")

        if delay_throttle_min:
            delay_throttle_min = int(delay_throttle_min)
            if delay_throttle_min > 0:
                start_date = datetime.strptime(
                    payload.get("start_date"), "%Y-%m-%dT%H:%M:%S"
                )
                end_date = datetime.utcnow() - timedelta(minutes=delay_throttle_min)
                if start_date > end_date:
                    return (
                        False,
                        "The Start Datetime should be less than 'Current UTC datetime - Delay Throttle(Minutes)' datetime.",
                    )
        return True, ""


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
        if address.startswith("[") and address.endswith("]"):
            address = address[1:-1]
            try:
                ipaddress.IPv6Address(address)
                return True
            except ipaddress.AddressValueError:
                return False
        return False

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


def graph_api_list_remove_item(confInfo, contentTypes):
    """This method is used to remove the content types from the list of inputs which are not part of
    the specific rest handler of graph_api. The graph_api resh handlers has common stanza for the inputs
    because of which it shows duplicate entries on the input page table. Hence this method implementation
    to return input entries only specific to particular rest handler based on content type.

    Args:
        confInfo (_type_): _description_
        contentTypes (_type_): list of content types of particular input type
    """

    config_items_copy = confInfo.data.copy()
    for key, value in config_items_copy.items():
        content_type = value.data.get("content_type")
        if not content_type in contentTypes:
            del confInfo.data[key]
