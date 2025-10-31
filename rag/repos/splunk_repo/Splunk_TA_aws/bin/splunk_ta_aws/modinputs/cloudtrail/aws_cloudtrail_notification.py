#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
"""
File for AWS cloudtrail notification.
"""
from __future__ import absolute_import

import json

import six

from .aws_cloudtrail_common import CloudTrailProcessorError


class NotificationProcessor:
    """
    CloudTrail/S3 Notification.
    """

    REQUIRED_FIELDS = ("Type", "MessageId", "TopicArn", "Message")

    @staticmethod
    def load(notification):
        """
        Load raw message from CloudTrail/S3 Notification.

        :param notification:
        :return:
        """
        if not NotificationProcessor.is_notification(notification):
            return notification
        try:
            msg_cont = json.loads(notification["Message"])
            if not isinstance(msg_cont, dict):
                raise Exception("Invalid message")
            return msg_cont
        except Exception:
            raise CloudTrailProcessorError(  # pylint: disable=raise-missing-from
                "Invalid CloudTrail message. Please check SQS settings."
            )

    @staticmethod
    def is_notification(notification):
        """
         It has these keys: "Type", "MessageId", "TopicArn", "Message",
         and the value of "Message" must be a string.

        :param notification:
        :return:
        """
        req_fields = NotificationProcessor.REQUIRED_FIELDS
        return all(f in notification for f in req_fields) and isinstance(
            notification["Message"], six.string_types
        )
