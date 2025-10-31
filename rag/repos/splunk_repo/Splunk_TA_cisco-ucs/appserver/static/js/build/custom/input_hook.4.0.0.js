/**
 *
 * SPDX-FileCopyrightText: 2024 Splunk, Inc.
 * SPDX-License-Identifier: LicenseRef-Splunk-8-2021
 *
 */

class InputHook {
  /**
   * Form hook
   * @constructor
   * @param {Object} globalConfig - Global configuration.
   * @param {object} serviceName - Service name
   * @param {object} state - Initial state of the form
   * @param {string} mode - edit,create or clone
   * @param {object} util - Object containing utility methods
   *                        {
   *                          setState,
   *                          setErrorMsg,
   *                          setErrorFieldMsg,
   *                          clearAllErrorMsg
   *                        }
   */
  constructor(globalConfig, serviceName, state, mode, util) {
    this.globalConfig = globalConfig;
    this.serviceName = serviceName;
    this.state = state;
    this.mode = mode;
    this.util = util;
  }
  /*
     Put logic here to execute javascript when UI gets rendered.
   */
  onRender() {
    /* Get window url to add redirect to Configuration page in servers field help text */
    var server_config_url = window.location.href.replace(
      "inputs",
      "configuration"
    );

    /* On load of Inputs page add help text under servers field */
    this.util.setState((prevState) => {
      let data = { ...prevState.data };
      data.servers.markdownMessage = {
        text: "Select one or more managers for the input or ##configure a new manager##",
        link: server_config_url,
        markdownType: "hybrid",
        token: "##configure a new manager##",
        linkText: "configure a new manager",
      };
      return { data };
    });
  }
}

export default InputHook;
