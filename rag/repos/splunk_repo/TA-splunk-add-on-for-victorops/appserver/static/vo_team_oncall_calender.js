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

    var tokenModel = mvc.Components.get('default');
    var submittedTokenModel = mvc.Components.getInstance('submitted');

    tokenModel.on("change:org_field", function(model, value) {
        console.log("Dropdown value changed: " + String(value));
        if (value != "*") {
          // unset any prior token
          tokenModel.unset("Slug");
          tokenModel.unset("form.Slug");
          submittedTokenModel.unset("Slug");
          submittedTokenModel.unset("form.Slug");
        }
    });
  })
})

