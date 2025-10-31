
import import_declare_test

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
import logging

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        'filter_type',
        required=True,
        encrypted=False,
        default='enrich',
        validator=None
    ), 
    field.RestField(
        'filter_value',
        required=True,
        encrypted=False,
        default=None,
        validator=None
    )
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    'splunk_ta_crowdstrike_fdr_cs_device_field_filters',
    model,
    config_name='cs_device_field_filters'
)


if __name__ == '__main__':
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
