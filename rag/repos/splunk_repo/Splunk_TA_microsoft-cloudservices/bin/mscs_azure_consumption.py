#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import import_declare_test
import sys

from modular_inputs.scripts.mscs_azure_consumption import MscsAzureConsumption

if __name__ == "__main__":
    exit_code = MscsAzureConsumption().run(sys.argv)
    sys.exit(exit_code)
