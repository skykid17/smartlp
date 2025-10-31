# encoding = utf-8

def process_event(helper, *args, **kwargs):
    """
    # IMPORTANT
    # Do not remove the anchor macro:start and macro:end lines.
    # These lines are used to generate sample code. If they are
    # removed, the sample code will not be updated when configurations
    # are updated.

    [sample_code_macro:start]

    # The following example gets the alert action parameters and prints them to the log
    mc_ueid = helper.get_param("mc_ueid")
    helper.log_info("mc_ueid={}".format(mc_ueid))

    ci = helper.get_param("ci")
    helper.log_info("ci={}".format(ci))

    summary = helper.get_param("summary")
    helper.log_info("summary={}".format(summary))

    impact = helper.get_param("impact")
    helper.log_info("impact={}".format(impact))

    urgency = helper.get_param("urgency")
    helper.log_info("urgency={}".format(urgency))

    incident_status = helper.get_param("incident_status")
    helper.log_info("incident_status={}".format(incident_status))

    incident_status_reason = helper.get_param("incident_status_reason")
    helper.log_info("incident_status_reason={}".format(incident_status_reason))

    work_info_details = helper.get_param("work_info_details")
    helper.log_info("work_info_details={}".format(work_info_details))

    custom_fields = helper.get_param("custom_fields")
    helper.log_info("custom_fields={}".format(custom_fields))


    # The following example adds two sample events ("hello", "world")
    # and writes them to Splunk
    # NOTE: Call helper.writeevents() only once after all events
    # have been added
    helper.addevent("hello", sourcetype="sample_sourcetype")
    helper.addevent("world", sourcetype="sample_sourcetype")
    helper.writeevents(index="summary", host="localhost", source="localhost")

    # The following example gets the events that trigger the alert
    events = helper.get_events()
    for event in events:
        helper.log_info("event={}".format(event))

    # helper.settings is a dict that includes environment configuration
    # Example usage: helper.settings["server_uri"]
    helper.log_info("server_uri={}".format(helper.settings["server_uri"]))
    [sample_code_macro:end]
    """

    helper.log_info("Alert action remedy_incident started.")

    # TODO: Implement your alert action logic here
    return 0
