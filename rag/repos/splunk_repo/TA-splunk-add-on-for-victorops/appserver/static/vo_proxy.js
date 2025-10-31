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

    let isAdmin = false;

    let roleSearchManager = new SearchManager({
      "id": "roleSearch",
      "status_buckets": 300,
      "search": '|rest splunk_server=local /services/authentication/current-context |table roles |mvexpand roles',
    });

    var roleResults = roleSearchManager.data("results", {count:0});

    roleResults.on("data", function() {
        console.log("Got Search Results");
        var d = roleResults.data();
        if (d && d.rows) {
            for (var i = 0; i < d.rows.length; i++) {
                if ( (d.rows[i][0] === 'admin') || (d.rows[i][0] === 'victorops_admin') || (d.rows[i][0] === 'sc_admin') ) {
                    isAdmin = true;
                    break;
                }
            }
        }
        if (isAdmin) {
            $("#protocol").removeAttr("disabled");
            $("#host").removeAttr("disabled");
            $("#port").removeAttr("disabled");
            $("#useAuth").removeAttr("disabled");
            $("#user").removeAttr("disabled");
            $("#password").removeAttr("disabled");
            $("#submit1").show();
            $("#delete1").show();
        }
    });

    roleSearchManager.startSearch();

    // Create a service object using the Splunk SDK for JavaScript
    // to send REST requests
    let service = mvc.createService({ owner: "nobody" , app: "TA-splunk-add-on-for-victorops"});

    let serviceParams = {
      output_mode: "JSON"
    };

    // Lookup proxy config and load UI fields.
    findProxy(function(result) {
      if (result) {
        if(result.user && result.user.length) {
          console.log('Loading UI with proxy coniguration with password.');
          // Lookup password then set fields.
          lookupPassword(result._key, function(value) {
            $('#protocol').val(result.protocol);
            $("#host").val(result.host);
            $("#port").val(result.port);
            $("#user").val(result.user);
            $("#key1").val(result._key); // Hidden field
            if (value) {
              $("#password").val(value);
            } else {
              console.error('User specified in Proxy Config but password not found!');
            }
            if (result.user.length > 0) {
              console.log('Authentication is enabled, setting checkbox and enabling user/password');
              $("#useAuth").prop('checked', true);
              $("#user").prop('disabled', false);
              $("#password").prop('disabled', false);
            } else {
              console.log('Authentication is dissabled, unchecking checkbox and disabling user/password');
              $("#useAuth").prop('checked', false);
              $("#user").prop('disabled', true);
              $("#password").prop('disabled', true);
            }
          });
        } else {
          console.log('Loading UI with proxy coniguration w/out password.');
           // No user / password display values from proxy config only.
          $('#protocol').val(result.protocol);
          $("#host").val(result.host);
          $("#port").val(result.port);
          $("#key1").val(result._key); // Hidden field
        }
      } else {
        console.log('Existing proxy config not found.');
      }
    });


    // Find the proxy entry in the kvstore, will invoke callback (cb) passing the _key of proxy if exists
    // or undefined if the entry does not exist.
    function findProxy(cb) {

      // For create, we need to lookup the _key in the kvstore. The key will be used for the
      // password and updated on the form.
      const query = '| inputlookup TA_splunk_add_on_for_victorops_proxy_lookup | table protocol,host,port,user,_key';

      const search = service.oneshotSearch(
        query,
        null,
        function(err,results) {

          if (err) {
            console.error('Proxy entry lookup error - ', err);
            return cb(undefined);
          }

          if (!results || !results.rows || results.rows.length === 0) {
            console.log ('proxy record does not exist in the the kvstore.');
            return cb(undefined);
          }

          // Add the new API to the kvstore
          const protocol = results.rows[0][0];
          const host = results.rows[0][1];
          const port = results.rows[0][2];
          const user = results.rows[0][3];
          const _key = results.rows[0][4];

          //console.log('Found proxy config entry in kvstore: protocol' + protocol + ', host: ' + host +
          //            ', port: ' + port + ', user: ' + user + ', _key: ' + _key);
          cb({ protocol, host, port, user, _key });
        });
    }

    function lookupPassword(key, cb) {
      // Retrieve API Key for previous version of the app.
      service.get("/servicesNS/nobody/TA-splunk-add-on-for-victorops/storage/passwords", serviceParams)
        .then(function(response) {
          const data = response;
          const pre_api = JSON.parse(data);

          //console.log('Found ' + pre_api.entry.length + ' storeage/password records to process.');

          let pass;
          for (let i = 0; i < pre_api.entry.length; i++) {
            const name = pre_api.entry[i].name;
            if (name && name.indexOf(key) !== -1) {
              //console.log('Found password entry for key: ', key);
              pass = pre_api.entry[i].content.clear_password;
              break;
            }
          }

          // API key does not exist, may not of have the previous version of the app.
          if (!pass || pass.length === 0) {
            cb(undefined);
          } else {
            cb(pass);
          }
        });
    }

    function deletePassword(key, cb) {
      lookupPassword(key, function(value) {
        if (value) {
          //console.log('Deleting storage password entry for _key: ' + key);
          service.del("storage/passwords/" + encodeURIComponent(key)).done(function() {
            console.log('Successfully removed storage/passwords api key entry!');
            cb();
          });
        } else {
          //console.log('Existing Password not found for key: ' + key);
          cb();
        }
      });
    }

    function createPassword(key, password, cb) {
      //console.log('Creating password entry for key: ' + key);
      // Create storage/password entry with user set to the Record's KV Store _key and password
      // as the unmasked API key.
      const body = 'name='+ encodeURIComponent(key)+ '&password='+ encodeURIComponent(password);
      service.request(
        "/servicesNS/nobody/TA-splunk-add-on-for-victorops/storage/passwords",
        "POST",
        null,
        null,
        body,
        {"Content-Type": "application/x-www-form-urlencoded"},
        null)
        .done(function () {
          cb();
        });
    }

    function createProxy(protocol, host,port,user,pass,cb) {
      // Create key
      const record = {
        "protocol": protocol,
        "host": host,
        "port": port,
        "user": user,
        "_key": ""
      };

      service.request(
        "storage/collections/data/TA_splunk_add_on_for_victorops_proxyconfig/",
        "POST",
        null,
        null,
        JSON.stringify(record),
        {"Content-Type": "application/json"},
        null)
        .done(function () {
          console.log('Successfully created proxy configuration in kvStore.');
          cb();
        });
    }

    function updateProxy(protocol, host,port,user,pass,key, cb) {

      // Search to update the proxy configuration entry in the kvstore with new values.
      const updateSearch = '| inputlookup TA_splunk_add_on_for_victorops_proxy_lookup ' +
        '| search _key=' + key +
        '| eval protocol="' + protocol + '" ' +
        '| eval host="' + host + '" ' +
        '| eval port=' + port + ' ' +
        '| eval user="' + user + '" ' +
        '| outputlookup TA_splunk_add_on_for_victorops_proxy_lookup append=True';
      //console.log('Updating proxy configuration for key: ' + key + ', search: ' + updateSearch);
      service.oneshotSearch(
        updateSearch,
        null,
        function (err, results) {
         //console.log('Successfully updated proxy configuration for key: ' + key);
         cb();
      });
    }

    // Create / Update proxy config. This involves:
    // 1. Create or update entry in the proxyconfig collection
    // 2. Delete password entry (which may not exist).
    // 3. Create password entry if password is present.
    function createProxyConfig(protocol,host,port,user,pass,key) {

      if (!key || !key.length) {
        createProxy(protocol,host,port,user,pass, function() {
          // Save password in secure storage.
          findProxy(function(proxyConfig) {
            if (!proxyConfig) {
              console.error('Failed find proxyConfig in kvStore!');
              alert ('Failed find proxy configuration in kvstore!');
              return;
            }
            const kvStoreKey = proxyConfig._key;
            // Update value of key1 hidden field. This is used in the update and delete scenarios.
            //console.log('Adding key: ' + kvStoreKey +' hidden field.');
            $("#key1").val(kvStoreKey);
              // Create the password.
            if (pass && pass.length) {
              createPassword(kvStoreKey, pass, function() {
                //console.log('Successfully saved created proxy password entry for key: ' + kvStoreKey);
                alert('Successfully created proxy configuration!');
              });
            } else {
                console.log('User and Password not specified, skipping creation of proxy of password entry.');
                alert('Successfully created proxy configuration!');
            }
          });
        });
      } else {
        // Update key.
        updateProxy(protocol,host,port,user,pass,key, function() {
          console.log('update proxy config done, updating password...');
          // For the case of update, cannot update a password in passwords/storage endpoint,
          // thus must delete then re-create (if password is specified).
          deletePassword(key, function() {
            console.log('Successfully deleted proxy configuration password entry.');
            if (pass && pass.length) {
              // Create the password.
              createPassword(key, pass, function() {
                //console.log('Saved created password for key: ' + key);
                alert('Successfully updated proxy configuration!');
              });
            } else {
              console.log('User / password not specified, not updating password entry.');
              alert('Successfully updated proxy configuration!');
            }
          });
        });
      }
    }

    function validateFormData() {
      const protocol = $('#protocol').val();
      const host = $("#host").val();
      const port = $("#port").val();
      const user = $("#user").val();
      const pass = $("#password").val();
      const key = $("#key1").val();
      if (!protocol || !host || !port) {
        alert('Missing Required fields!');
        return false;
      }

      if (user && user.length && (!pass || pass.length === 0)) {
        alert('Password must be specified when user is present.')
        return false;
      }

      if (pass && pass.length && (!user || user.length === 0)) {
        alert('User must be specified when password is present.')
        return false;
      }

      let numericPort = Number(port);
      if (!numericPort) {
        alert('Port must be numeric');
        return false;
      }
      return true;
    }

    // Use Authentication Checkbox
    $("#useAuth").on("click", function(e) {
      if($(this).is(":checked")) {
        console.log('The check box is checked!');
        $("#user").prop('disabled', false);
        $("#password").prop('disabled', false);
      } else {
        console.log('The check box is NOT checked!');
        $("#user").prop('disabled', true);
        $("#password").prop('disabled', true);
        $("#user").val('');
        $("#password").val('');
      }
    });

    // Submit Button
    $("#submit1").on("click", function (e) {
      if (!validateFormData()) {
        // Invalid form data
        return;
      }
      const protocol = $('#protocol').val();
      const host = $("#host").val();
      const port = $("#port").val();
      const user = $("#user").val();
      const pass = $("#password").val();
      const key = $("#key1").val();
      createProxyConfig(protocol,host,port,user,pass,key);
    });

    // Delete button.
    $("#delete1").on("click", function (e) {
      const key = $("#key1").val();
      if (key && key.length) {
          if (confirm("Are you sure you want to delete Proxy Configuration?") == true) {
          //console.log('Deleting proxy config for _key: ' + key);
          service.del("storage/collections/data/TA_splunk_add_on_for_victorops_proxyconfig/" + encodeURIComponent(key)).done(function () {
            deletePassword(key, function () {
              // Delete done Clear fields.
              $('#protocol').val('');
              $("#host").val('');
              $("#port").val('');
              $("#user").val('');
              $("#password").val('');
              $("#key1").val('');
            });
          });
        } else {
            console.log('Proxy config delete cancelled by user.');
          }
      } else {
        console.log('Delete clicked but found nothing to delete.');
      }
    });
  });
});

