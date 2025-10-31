#
# SPDX-FileCopyrightText: 2021 Splunk, Inc. <sales@splunk.com>
# SPDX-License-Identifier: LicenseRef-Splunk-8-2021
#
#

import logging
from splunk import ResourceNotFound
from splunktaucclib.rest_handler import base, multimodel
from splunktaucclib.rest_handler.error_ctl import RestHandlerError as RH_Err
from splunktaucclib.rest_handler.util import makeConfItem


class BaseHandlerWrapper:

    # TODO: migrate BaseRestHandler to AdminExternalHandler - https://splunk.atlassian.net/browse/ADDON-79487
    # Overridden handleList method to eliminate reload calls
    def handleList(self, confInfo):
        user, app = self.user_app()

        # Read configuration
        if self.callerArgs.id is None:
            ents = self.all()
            for name, ent in ents.items():
                makeConfItem(name, ent, confInfo, user=user, app=app)
        else:
            try:
                ent = self.get(self.callerArgs.id)
                makeConfItem(self.callerArgs.id, ent, confInfo, user=user, app=app)
            except ResourceNotFound as exc:
                RH_Err.ctl(-1, exc, logLevel=logging.INFO)


class BaseRestHandlerWrapper(BaseHandlerWrapper, base.BaseRestHandler):
    def __init__(self, *args, **kwargs):
        base.BaseRestHandler.__init__(self, *args, **kwargs)


class MultiModalRestHandlerWrapper(
    BaseHandlerWrapper, multimodel.MultiModelRestHandler
):
    def __init__(self, *args, **kwargs):
        multimodel.MultiModelRestHandler.__init__(self, *args, **kwargs)
