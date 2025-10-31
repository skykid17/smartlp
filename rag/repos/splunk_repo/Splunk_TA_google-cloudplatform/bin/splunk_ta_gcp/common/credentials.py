#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#
import json
from builtins import object

import google.auth


class CredentialFactory(object):
    def __init__(self, config):
        self._config = config

    def load(self, profile, scopes):
        collection = "splunk_ta_google/google_credentials"
        content = self._config.load(
            collection, stanza=profile, virtual=True, clear_cred=True
        )
        content["scopes"] = scopes
        return self.get_credential(content)

    @staticmethod
    def get_credential(config):
        """
        Get credential of any account_type and create a credential
        object
        """
        google_cred = config.get("google_credentials")
        scopes = config.get("scopes")
        if isinstance(google_cred, str):
            google_cred = json.loads(google_cred)

        # if no cred found, try default() to fetch credential
        # from environment variable GOOGLE_APPLICATION_CREDENTIALS
        # or running in google compute engine
        if google_cred:
            credential, _ = google.auth.load_credentials_from_dict(
                google_cred, scopes=scopes
            )
        else:
            credential, _ = google.auth.default()

        return credential
