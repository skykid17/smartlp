/*
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
  constructor (globalConfig, serviceName, state, mode, util) {
    this.globalConfig = globalConfig
    this.serviceName = serviceName
    this.state = state
    this.mode = mode
    this.util = util
  }

  /*
          Put logic here to execute javascript when UI gets rendered.
      */
  onRender () {
    /* Get window url to add redirect to Configuration page in account field help text */
    const AccountConfigUrl = window.location.href.replace(
      'inputs',
      'configuration'
    )
    const fieldsToDisable = [
      'object_name',
      'operation_name',
      'signature',
      'params',
      'split_array'
    ]

    /* On load of Inputs page add help text under account field and disable 5 fields */
    this.util.setState((prevState) => {
      const data = { ...prevState.data }
      data.account.markdownMessage = {
        text: 'Select an account. Additional accounts may be configured from ##here##',
        link: AccountConfigUrl,
        markdownType: 'hybrid',
        token: '##here##',
        linkText: 'here'
      }
      fieldsToDisable.forEach((field) => {
        data[field].disabled = true
      })
      return { data }
    })
  }
}

export default InputHook
