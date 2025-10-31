#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import sys
import traceback

# isort: off
import import_declare_test  # noqa: F401
from Splunk_TA_github_connect import GitHubConnect
from Splunk_TA_github_utils import get_account_details, get_proxy_settings, set_logger
from splunklib import modularinput as smi
from solnlib import log
import Splunk_TA_github_consts as constants


class GITHUB_AUDIT_INPUT(smi.Script):
    def __init__(self):
        super(GITHUB_AUDIT_INPUT, self).__init__()

    def get_scheme(self):
        scheme = smi.Scheme("github_audit_input")
        scheme.description = "GitHub Input"
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = False

        scheme.add_argument(
            smi.Argument(
                "name", title="Name", description="Name", required_on_create=True
            )
        )

        scheme.add_argument(
            smi.Argument(
                "account_type",
                required_on_create=True,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "org_name",
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "enterprises_name",
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "use_existing_checkpoint",
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "start_date",
                required_on_create=False,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "events_type",
                required_on_create=True,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "account",
                required_on_create=True,
            )
        )

        scheme.add_argument(
            smi.Argument(
                "input_type",
                required_on_create=False,
            )
        )

        return scheme

    def validate_input(self, definition):
        return

    def stream_events(self, inputs, event_writer):
        """
        This method is invoked for each input repeatedly at configured interval
        :param inputs: Input arguments for the particular modular input
        :param event_writer: Event Writer object
        """

        self.session_key = self._input_definition.metadata["session_key"]
        _logger = set_logger(
            self.session_key,
            "Splunk_TA_github_audit_input_"
            + (list(inputs.inputs.keys())[0]).split("//")[1],
        )

        try:
            for input_name, input_items in inputs.inputs.items():
                input_items["name"] = input_name

            account_name = input_items.get("account")
            account_details = get_account_details(
                _logger, self.session_key, account_name
            )

            account_type = input_items["account_type"]
            if account_type == "orgs":
                org_name = input_items["org_name"]
            else:
                org_name = input_items["enterprises_name"]

            config = {
                "session_key": self.session_key,
                "input_params": input_items,
                "logger": _logger,
                "account_name": account_name,
            }
            config.update(account_details)
            config["proxies"] = get_proxy_settings(_logger, self.session_key)

            obj = GitHubConnect(config)
            obj.collect_audit_data(account_type, org_name)
        except Exception as e:
            _logger.error("Error in Modular Input: {}".format(traceback.format_exc()))
            log.log_exception(
                _logger,
                e,
                exc_label=constants.UCC_EXECPTION_EXE_LABEL,
                msg_before="Unexpected error occurred in the Modular Input.",
            )


if __name__ == "__main__":
    exit_code = GITHUB_AUDIT_INPUT().run(sys.argv)
    sys.exit(exit_code)
