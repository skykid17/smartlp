require.config({
  paths: {
  'app': '../app'
  }
});

require([
  "underscore",
  "jquery",
  "splunkjs/mvc/utils",
  "splunkjs/mvc",
  "splunkjs/mvc/tokenutils",
  "splunkjs/mvc/simplexml",
  "splunkjs/mvc/layoutview",
  "splunkjs/mvc/simplexml/dashboardview",
  "splunkjs/mvc/simplexml/dashboard/panelref",
  "splunkjs/mvc/simplexml/element/chart",
  "splunkjs/mvc/simplexml/element/event",
  "splunkjs/mvc/simplexml/element/html",
  "splunkjs/mvc/simplexml/element/list",
  "splunkjs/mvc/simplexml/element/map",
  "splunkjs/mvc/simplexml/element/single",
  "splunkjs/mvc/simplexml/element/table",
  "splunkjs/mvc/simplexml/element/visualization",
  "splunkjs/mvc/simpleform/formutils",
  "splunkjs/mvc/simplexml/eventhandler",
  "splunkjs/mvc/simplexml/searcheventhandler",
  "splunkjs/mvc/simpleform/input/dropdown",
  "splunkjs/mvc/simpleform/input/radiogroup",
  "splunkjs/mvc/simpleform/input/linklist",
  "splunkjs/mvc/simpleform/input/multiselect",
  "splunkjs/mvc/simpleform/input/checkboxgroup",
  "splunkjs/mvc/simpleform/input/text",
  "splunkjs/mvc/simpleform/input/timerange",
  "splunkjs/mvc/simpleform/input/submit",
  "splunkjs/mvc/searchmanager",
  "splunkjs/mvc/savedsearchmanager",
  "splunkjs/mvc/postprocessmanager",
  "splunkjs/mvc/simplexml/urltokenmodel",
  "splunkjs/mvc/tableview",
  "splunkjs/mvc/simplexml/ready!"
], function(
  _,
  $,
  utils,
  mvc,
  TokenUtils,
  DashboardController,
  LayoutView,
  Dashboard,
  PanelRef,
  ChartElement,
  EventElement,
  HtmlElement,
  ListElement,
  MapElement,
  SingleElement,
  TableElement,
  VisualizationElement,
  FormUtils,
  EventHandler,
  SearchEventHandler,
  DropdownInput,
  RadioGroupInput,
  LinkListInput,
  MultiSelectInput,
  CheckboxGroupInput,
  TextInput,
  TimeRangeInput,
  SubmitButton,
  SearchManager,
  SavedSearchManager,
  PostProcessManager,
  UrlTokenModel,
  TableView
) {
  require(["splunkjs/mvc/simplexml/ready!"], function () {
    console.log("Loading Javascript ...");
    var tokenModel = mvc.Components.get('default')
    var org = "*";
    tokenModel.on("change:org_field", function(model, value) {
        console.log("Dropdown value changed: " + String(value));
        //getUsers("*");
        getPolicies(value);
    });

    var organizationSearchManager = null;
    function getOrganizations() {
        var organizationSearch = "`victorops_incidents` org != '' | eval name = org | dedup name | sort name  | table name";
        if (organizationSearchManager == null) {
            organizationSearchManager = new SearchManager({
                "id": "organizationSearch",
                "status_buckets": 300,
                "search": organizationSearch
            });
            var organizationResults = organizationSearchManager.data("results", {count:0});

            organizationResults.on("data", function() {
                console.log("Got Organization Search Results");
                var d = organizationResults.data();
                var html = "";
                if (d && d.rows) {
                    if (d.rows.length == 0) {
                        html = '<option value="'+d.rows[0]+'" selected="selected">'+d.rows[0]+'</option>';  
                    }
                    else {
                        html = '<option value="">Select Organization</option>';  
                        for (var i = 0; i < d.rows.length; i++) {
                            html += '<option value="'+d.rows[i]+'">'+d.rows[i][0]+'</option>';
                        }
                    }
                    $("#orgSelect").html(html);
                }
            });
        }
        else {
            organizationSearchManager.query.set("search", policySearch);
        }
    }
    getOrganizations();

    var policySearchManager = null;
    function getPolicies(org) {
        console.log("getPolicies("+org+")");
        //var org = tokenModel.get("org_field");
        var policySearch = "`victorops_teams` type=\"team\" org=\""+org+"\" | eval policies = 'policies{}.name' | eval policies_slug = 'policies{}.slug' | eval team = 'info.name' | mvexpand policies | mvexpand policies_slug | dedup policies | sort policies | eval row =team+\" - \"+policies | table row policies_slug | sort row";

        if (policySearchManager == null) {
            policySearchManager = new SearchManager({
                "id": "policySearch",
                "status_buckets": 300,
                "search": policySearch
            });
            var policyResults = policySearchManager.data("results", {count:0});

            policyResults.on("data", function() {
                console.log("Got Policy Search Results");
                var d = policyResults.data();
                if (d && d.rows) {
                    var html = '<option value="" disabled="disabled" selected="selected">Select Team - Policy</option>';  
                    for (var i = 0; i < d.rows.length; i++) {
                        html += '<option value="'+d.rows[i][1]+'">'+d.rows[i][0]+'</option>';
                    }
                    $("#teamSelect").html(html);
                }
            });
        }
        else {
            policySearchManager.query.set("search", policySearch);
            //policySearchManager.startSearch();
        }
    }
    getPolicies("*");

    var userSearchManager = null;
    function getUsers(policy) {
        console.log("getUsers("+policy+")");
        var org = tokenModel.get("org_field");
        //var userSearch = "`victorops_teams` "+policy+" info.name=\""+team+"\" | eval users = 'members{}.username' | mvexpand users | dedup users | sort users | table users";
        //var userSearch = "`victorops_teams` "+policy+" | eval users = 'members{}.username' | mvexpand users | dedup users | sort users | table users";
        //var userSearch = "`victorops_teams`| eval users = 'members{}.username' | mvexpand users | eval policies = 'policies{}.slug' | mvexpand policies | dedup users | sort users | search policies="+policy+" | table users";
        //var userSearch = "`victorops_teams` org=\""+org+"\" | eval users = 'members{}.username' | mvexpand users | eval policies = 'policies{}.slug' | mvexpand policies | dedup users | sort users | search policies="+policy+" | table users | join users [search `victorops_users` org=\""+org+"\" earliest=0 | dedup info.username | eval users='info.username' | eval displayName='info.displayName'+\" (\"+users+\")\"| table users displayName]";
        var userSearch = "`victorops_teams` org=\""+org+"\" | eval users = 'members{}.username' | mvexpand users | eval policies = 'policies{}.slug' | mvexpand policies | dedup users | sort users | search policies="+policy+" | table users | join users [search `victorops_users` org=\""+org+"\" earliest=0 | dedup info.username | eval users='info.username' | eval displayName='info.displayName'| table users displayName] | table users displayName";
        console.log("userSearch="+userSearch);
        if (userSearchManager == null) {
            userSearchManager = new SearchManager({
                "id": "userSearch",
                "status_buckets": 300,
                "search": userSearch
            });
            var userResults = userSearchManager.data("results", {count:0});

            userResults.on("data", function() {
                console.log("Got User Search Results");
                var d = userResults.data();
                if (d && d.rows) {
                    var html = '<option value="" disabled="disabled" selected="selected">Select User</option>';  
                    for (var i = 0; i < d.rows.length; i++) {
                        html += '<option value="'+d.rows[i][0]+'">'+d.rows[i][1]+' ('+d.rows[i][0]+')</option>';
                    }
                    $("#userSelect").html(html);
                }
            });
        }
        else {
            userSearchManager.query.set("search", userSearch);
            //userSearchManager.startSearch();
        }
    }
    getUsers("*");

    var conferenceBridgeSearchManager = null;
    function getConferenceBridges() {
        var conferenceBridgeSearch = "| getConferenceBridges ";
        if (conferenceBridgeSearchManager == null) {
            conferenceBridgeSearchManager = new SearchManager({
                "id": "conferenceBridgeSearch",
                "status_buckets": 300,
                "search": conferenceBridgeSearch
            });
            var conferenceBridgeResults = conferenceBridgeSearchManager.data("results", {count:0});

            conferenceBridgeResults.on("data", function() {
                console.log("Got create response");
                var d = conferenceBridgeResults.data();
                for (var i = 0; i < d.rows.length;i++) {
                    var row = d.rows[i]
                }
            });
        }
        else {
            conferenceBridgeSearchManager.query.set("search", conferenceBridgeSearch);
            //conferenceBridgeSearchManager.startSearch();
        }
    }
    //getConferenceBridges();

    var createIncidentSearchManager = null;
    function createIncident(incident) {
        console.log("createIncident() entry ...");
        //var createIncidentSearch = "| createVOIncident '" + JSON.stringify(incident).replace(/"/g, '\"') + "'";
        var createIncidentSearch = "| createVOIncident ";
        createIncidentSearch += ' org="'+incident.org_slug+'"';
        createIncidentSearch += ' summary="'+incident.summary+'"';
        createIncidentSearch += ' details="'+incident.details+'"';
        createIncidentSearch += ' username="'+incident.username+'"';
        createIncidentSearch += ' target_type="'+incident.targets[0].type+'"';
        createIncidentSearch += ' target_slug="'+incident.targets[0].slug+'"';
        createIncidentSearch += ' ismultiresponder="'+incident.isMultiResponder+'"';
        if (incident.conferenceBridge) {
          createIncidentSearch += ' bridge_url="'+incident.conferenceBridge.url+'"';
          createIncidentSearch += ' bridge_phone="'+incident.conferenceBridge.phone+'"';
          createIncidentSearch += ' bridge_notes="'+incident.conferenceBridge.notes+'"';
        }
        console.log("search="+createIncidentSearch);

        if (createIncidentSearchManager == null) {
            createIncidentSearchManager = new SearchManager({
                "id": "createIncidentSearch",
                "status_buckets": 300,
                "search": createIncidentSearch
            });
            var createIncidentResults = createIncidentSearchManager.data("results", {count:0});

            createIncidentResults.on("data", function() {
                console.log("Got create response");
                var d = createIncidentResults.data();
                var tmp = d.rows[0];
                tmp = tmp[0];
                if (tmp.startsWith("Failure")) {
                    console.log(tmp);
                    $("#dialogErrorMessage").html("Failure Creating Incident!");
                }
                else {
                    var incidentNumber = tmp;

                    $('#createModal').css('z-index', '-9999');
                    $('#createModal').modal('hide');

                    // Display modal indicating Incident # Created
                    $('#incidentModalBody').html("Incident #" + incidentNumber + " created!");
                    $('#incidentModal').css('z-index', '9999');
                    $('#incidentModal').modal('show');
                }
            });
            createIncidentResults.on("search:error", function(properties) {
                console.log("search:error", properties);
            });
            createIncidentResults.on("search:done", function(properties) {
                console.log("search:done", properties);
            });
        }
        else {
            createIncidentSearchManager.query.set("search", createIncidentSearch);
            //createIncidentSearchManager.startSearch();
        }
    }

    var html = '<div style="display:inline-block;float:right;height:50px;vertical-align:top;margin-top:23px;"><input id="addIncidentButton" class="btn btn-vo" value="Create Incident" style="white-space: nowrap; width: 150px; height: 35px; margin-bottom: 0px;" type="button"></div>';
    $("#fieldset1").append(html);

    // Delete button.
    $("#addIncidentButton").on("click", function (e) {
        e.preventDefault();
        console.log("Button Click");
        //getUsers("*");


        // Reset Fields
        $("#orgSelect").val("");
        $("#teamSelect").val("");
        $("#userSelect").val("");
        $("#behaviorSelect").val("false");
        $("#descriptionTI").val("");
        $("#incidentDetailTA").val("");
        $("#bridgeSelect").val("");
        $("#urlTI").val("");
        $("#phoneTI").val("");
        $("#notesTA").val("");
        
        $("#dialogErrorMessage").html("");
        $("#enterBridgePanel").hide();
        $('#createModal').css('z-index', '9999');
        $('#createModal').modal('show');
    });

    $("#bridgeSelect").on("change", function(e) {
        e.preventDefault();
        var tmp = $(this).val();
        console.log("Bridge Select " + tmp);
        if (tmp == "-1") {
            $("#enterBridgePanel").show();
            $("#createModal").css("height","700px");
            $("#createModalBody").css("min-height","610px");
        }
        else {
            $("#enterBridgePanel").hide();
            $("#createModal").css("height","620px");
            $("#createModalBody").css("min-height","470px");
        }
    
    });

    $("#orgSelect").on("change", function(e) {
        e.preventDefault();
        var tmp = $(this).val();
        getPolicies(tmp);
    });

    $("#teamSelect").on("change", function(e) {
        e.preventDefault();
        var tmp = $(this).val();
        //if (tmp != "") {
        //    var value = tmp.split(" - ");
        //    getUsers(value[0],value[1]);
        //}
        //else {
        //    getUsers("","*");
        //}
        // Uncomment if you want to limit users to only those associated to policy
        getUsers(tmp);
    });

    var old_timestamp = null;
    $("#createDialogButton").on("click", function(e) {
        e.preventDefault();
        if(old_timestamp == null || old_timestamp + 1000 < event.timeStamp) {
            old_timestamp = event.timeStamp;
            $("#dialogErrorMessage").html("");
            var org = $("#orgSelect").val();
            var policy = $("#teamSelect").val();
            var user = $("#userSelect").val();
            var behavior = $("#behaviorSelect").val();
            var description = $("#descriptionTI").val();
            var incidentDetail = $("#incidentDetailTA").val();
            var bridge = $("#bridgeSelect").val();
            var url = $("#urlTI").val();
            var phone = $("#phoneTI").val();
            var notes = $("#notesTA").val();

            if (org == null || org == "") {
                $("#dialogErrorMessage").html("Organization is a required field!");
                return;
            }
            else if (policy == null || policy == "") {
                $("#dialogErrorMessage").html("Team/Policy is a required field!");
                return;
            }
            else if (user == null || user == "") {
                $("#dialogErrorMessage").html("User is a required field!");
                return;
                //user = "system";
            }
            else if (behavior == "") {
                $("#dialogErrorMessage").html("Acknowledge Behavior is a required field!");
                return;
            }
            else if (description == "") {
                $("#dialogErrorMessage").html("Incident Description is a required field!");
                return;
            }
            else if (incidentDetail == "") {
                $("#dialogErrorMessage").html("Incident Body is a required field!");
                return;
            }

            var d = {
                summary: description,
                details: incidentDetail,
                username: user,
                targets: [
                    {
                        type: "EscalationPolicy",
                        slug: policy
                    }
                ],
                isMultiResponder: true,
                org_slug: org
            };

            console.log("bridge="+bridge);
            if (bridge == "-1") {
                d.conferenceBridge = {
                    url: url,
                    phone: phone,
                    notes: notes
                };
            }
            createIncident(d);
            this.disabled=false;
        }
    });
  })
})

