#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

from azure.identity import ClientSecretCredential
from logging import Logger
from splunk_ta_mscs.models import AzureAccountConfig


def get_credential(
    account: AzureAccountConfig, proxies: dict
) -> ClientSecretCredential:
    return ClientSecretCredential(
        client_id=str(account.client_id),
        client_secret=account.client_secret,
        tenant_id=str(account.tenant_id),
        authority=account.class_type.authority_url,
        proxies=proxies,
    )


def validate_credential(account: AzureAccountConfig, proxies: dict, logger: Logger):
    try:
        credential = get_credential(account, proxies)
        scope = f"{account.class_type.cloud_environment.endpoints.resource_manager}/.default"
        credential.get_token(scope)
    except Exception as e:
        logger.error("Credential validation failed", exc_info=e)
        raise

    _check_account_class_type(credential, account.class_type.authority_url, logger)


def _check_account_class_type(
    credential: ClientSecretCredential, authority_url: str, logger: Logger
):
    authorization_endpoint = credential._get_app().authority.authorization_endpoint
    try:
        authorization_endpoint.index(authority_url)
    except ValueError:
        logger.error(
            f"Actual authorization endpoint ({authorization_endpoint}) does not match expected authority ({authority_url})"
        )
        raise
