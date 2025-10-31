#
# SPDX-FileCopyrightText: 2024 Splunk, Inc.
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

"""
This file consists constants used in the /bin module
"""
import os.path as op

APP_NAME = __file__.split(op.sep)[-3]
CONNECTION_ERROR = "log_connection_error"
CONFIGURATION_ERROR = "log_configuration_error"
PERMISSION_ERROR = "log_permission_error"
AUTHENTICATION_ERROR = "log_authentication_error"
SERVER_ERROR = "log_server_error"
GENERAL_EXCEPTION = "log_exception"
CYBERARK_EPM_ERROR = "cyberark_epm_ta_error"
UCC_EXECPTION_EXE_LABEL = "splunk_ta_cyberark_epm_exception_{}"
PAGE_LIMIT = 500
ACCOUNT_ADMIN_SOURCETYPE = "cyberark:epm:account:admin:audit"
API_TIME_OUT = 120
