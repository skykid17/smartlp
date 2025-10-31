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

    console.log("loading javascript ...");

    // Create a service object using the Splunk SDK for JavaScript
    // to send REST requests
    let service = mvc.createService({ owner: "nobody" , app: "TA-splunk-add-on-for-victorops"});

    let isAdmin = false;

    let roleSearchManager = new SearchManager({
      "id": "roleSearch",
      "status_buckets": 300,
      "search": '|rest splunk_server=local /services/authentication/current-context |table roles |mvexpand roles',
    });

    var roleResults = roleSearchManager.data("results", {count:0});

    var roleResults = roleSearchManager.data("results", {count:0});
    roleResults.on("data", function() {
        console.log("Got Role Results");
        var d = roleResults.data();
        if (d && d.rows) {
            for (var i = 0; i < d.rows.length; i++) {
                if ( (d.rows[i][0] === 'admin') || (d.rows[i][0] === 'victorops_admin') || (d.rows[i][0] === 'sc_admin') ) {
                    //$("#configPanel").show();
                    isAdmin = true;
                    break;
                }
            }
        }
        //$("#mainPanel").show();
        $("#slaPanel").show();
    });
    roleSearchManager.startSearch();

    function createSLA(mtta,mttr,cb) {
      let pMTTA = (mtta === undefined) ? 60 : mtta;
      let pMTTR = (mttr === undefined) ? 240 : mttr;
      // Create key
      const record = {
        "mtta": pMTTA,
        "mttr": pMTTR,
        "_key": ""
      };

      service.request(
        "storage/collections/data/victorops_sla/",
        "POST",
        null,
        null,
        JSON.stringify(record),
        {"Content-Type": "application/json"},
        null)
        .done(function () {
          console.log('Successfully created SLA record in kvStore.');
          cb();
        });
    }

    function updateSLA(mtta,mttr,key,cb) {

      // Search to update the proxy configuration entry in the kvstore with new values.
      const updateSearch = '| inputlookup victorops_sla_lookup ' +
        '| search _key=' + key +
        '| eval mtta="' + mtta+ '"' +
        '| eval mttr="' + mttr + '"' +
        '| outputlookup victorops_sla_lookup append=True';
      service.oneshotSearch(
        updateSearch,
        null,
        function (err, results) {
         //console.log('Successfully updated alert recovery configuration for key: ' + key);
         cb();
      });
    }


    function createSLAConfig(mtta, mttr, key) {
      if (!mtta || !mttr) {
        // Create
        createSLA(mtta,mttr, function() {
          // Lookup record and update hidden field key1.
          getSLA(function(slaConfig) {
            if (!slaConfig) {
              console.error('Failed find sla config in kvStore!');
              //alert('Failed find SLA config in kvstore!');
              return;
            }
            const kvStoreKey = slaConfig._key;
            // Update value of key1 hidden field. This is used in the update and delete scenarios.
            $("#key1").val(kvStoreKey);
          });
        });
      } else {
        // Update key.
        updateSLA(mtta,mttr,key, function() {});
      }
    }

    function getSLA(cb) {

      // For create, we need to lookup the _key in the kvstore. The key will be used for the
      // password and updated on the form.
      const query = '| inputlookup victorops_sla_lookup | table mtta,mttr,_key';

      const search = service.oneshotSearch(
        query,
        null,
        function(err,results) {

          if (err) {
            console.error('SLA entry lookup error - ', err);
            return cb(undefined);
          }

          if (!results || !results.rows || results.rows.length === 0) {
            console.log ('SLA record does not exist in the the kvstore.');
            return cb(undefined);
          }

          // Add the new API to the kvstore
          const mtta = results.rows[0][0];
          const mttr = results.rows[0][1];
          const _key = results.rows[0][2];

          //console.log('Found alert recovery config entry in kvstore: enabled [' + enabled +
          //            '], pollingInterval: ' + pollingInterval + ', numPeriods: ' + numPeriods + ', _key: ' + _key);
          cb({ mtta, mttr, _key });
        });
    }

    getSLA(function(result) {
        if (result) {
            $("#key1").val(result._key); // Load form's Hidden field
            console.log('SLA is configured.');
            $("#mtta").val(result.mtta);
            $("#mttr").val(result.mttr);
            if (isAdmin) {
                $("#mtta").removeAttr('disabled');
                $("#mttr").removeAttr('disabled');
            }
        } 
        else {
            // Not yet defined, use default values.
            console.log('sla configuration does not yet exist, creating entry with default values.');
            // Create SLA configuration with default values.
            createSLA(60,240,function() {});

            $("#mtta").val('60'); // 60 minutes 
            $("#mttr").val('240'); // 240 minutes

            if (isAdmin) {
              $("#mtta").removeAttr('disabled');
              $("#mttr").removeAttr('disabled');
            }
            else {
                $("#mtta").attr('disabled', 'disabled');
                $("#mttr").attr('disabled', 'disabled');
            }
        }
    })

    $(".numbers-only").keypress(function (e) {
        // Allow: backspace/delete, tab, and enter
        if ($.inArray(e.keyCode, [8, 9, 13]) !== -1) {
            return;
        }

        var code = e.which || e.keyCode;
        var charStr = String.fromCharCode(code);
        if (/[0-9]/.test(charStr)) return;

        e.preventDefault();
    });

    $("#submit").on("click", function(e) {
        console.log("Submit Click");
        var mtta = $("#mtta").val();
        var mttr = $("#mttr").val();
        var key = $("#key1").val();
        createSLAConfig(mtta,mttr,key);
    });

    //console.log("javascript load done ...");
    //getSLA();
  });
});

