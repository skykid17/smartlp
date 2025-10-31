/**
 *
 * SPDX-FileCopyrightText: 2024 Splunk, Inc.
 * SPDX-License-Identifier: LicenseRef-Splunk-8-2021
 *
 */

class Hook {
  constructor(globalConfig, serviceName, state, mode, util) {
    this.globalConfig = globalConfig
    this.serviceName = serviceName
    this.state = state
    this.mode = mode
    this.util = util
    this._debouncedValueChange = this.debounce(
      this._valueChange.bind(this),
      200
    )
    this._startDateChange = this.debounce(this._startDateChange.bind(this), 200)
  }

  onCreate() {
    // No implementation required as of now
  }

  debounce(func, wait) {
    let timeout
    // This is the function that is returned and will be executed many times
    // We spread (...args) to capture any number of parameters we want to pass
    return function executedFunction(...args) {
      // The callback function to be executed after
      // the debounce time has elapsed
      // This will reset the waiting every function execution.
      // This is the step that prevents the function from
      // being executed because it will never reach the
      // inside of the previous setTimeout
      clearTimeout(timeout)

      // Restart the debounce waiting period.
      // setTimeout returns a truthy value
      timeout = setTimeout(() => {
        func(...args)
      }, wait)
    }
  }

  onChange(field, value, dataDict) {
    if (this.serviceName === 'inbox_events' || this.serviceName === 'policy_audit_events' || this.serviceName === 'admin_audit_logs' || this.serviceName === 'account_admin_audit_logs') {
      var oldStartDate = this.state.data.start_date.value
      this.util.setState(prevState => {
        const data = {
          ...prevState.data
        }
        if (field === 'use_existing_checkpoint' && data.use_existing_checkpoint.value === "1") {
          data.start_date.value = oldStartDate
        }
        if (field === 'start_date' && this.mode === 'edit') {
          this._startDateChange(oldStartDate, dataDict)
        }
        return {
          data
        }
      })
    }
    else if (this.serviceName === 'policies_and_computers') {
      var value = this.state.data.collect_data_for.value // eslint-disable-line
      if (field === 'collect_data_for') {
        this._debouncedValueChange(field, value, dataDict)
      }
    }
    else if (this.serviceName === 'application_events' || this.serviceName === 'threat_detection') {
      this.util.setErrorMsg("This Input is Deprecated. Please utilize the new Input - Inbox Events")
    }
    else if (this.serviceName === 'policy_audit') {
      this.util.setErrorMsg("This Input is Deprecated. Please utilize the new Input - Policy Audit Events")
    }
  }

  onRender() {
    this.util.setState(prevState => {
      const data = { ...prevState.data }
      if (this.mode === 'edit') {
        if (
          this.serviceName === 'inbox_events' ||
          this.serviceName === 'policy_audit_events' ||
          this.serviceName === 'admin_audit_logs' ||
          this.serviceName === 'account_admin_audit_logs'
        ) {
          data.use_existing_checkpoint.display = true
          data.use_existing_checkpoint.value = 'yes'
          data.use_existing_checkpoint.markdownMessage = {
            text: 'A Checkpoint for this input already exists. Selecting `No` will reset the data collection.',
            color: 'red',
            markdownType: 'text'
          }
          data.start_date.disabled = true
        }
      }
      if (this.mode === "create") {
        if (
          this.serviceName === 'inbox_events' ||
          this.serviceName === 'policy_audit_events' ||
          this.serviceName === 'admin_audit_logs' ||
          this.serviceName === 'account_admin_audit_logs'
        ) {
          const now = new Date();
          now.setMinutes(now.getMinutes() - 6);
          const currentDateTime = now.toISOString();
          data.start_date.value = currentDateTime.substring(0, 19) + 'Z';
        }
      }
      if (this.serviceName === 'policies_and_computers') {
        const newValue1 = this.state.data.collect_data_for.value
        const optionList = newValue1.split(',')

        if (!optionList.includes('policies')) {
          data.collect_policy_details.value = 0
          data.collect_policy_details.disabled = true
        }
      }
      else if (this.serviceName === 'application_events' || this.serviceName === 'threat_detection') {
        this.util.setErrorMsg("This Input is Deprecated. Please utilize the new Input - Inbox Events")
      }
      else if (this.serviceName === 'policy_audit') {
        this.util.setErrorMsg("This Input is Deprecated. Please utilize the new Input - Policy Audit Events")
      }
      return { data }
    })
  }

  onSave(dataDict) {
    this.util.setState(prevState => {
      const data = { ...prevState.data }
      if (this.serviceName === 'policies_and_computers') {
        const newValue = dataDict.collect_data_for
        const optionList = newValue.split(',')

        if (!optionList.includes('policies')) {
          data.collect_policy_details.value = 0
        }
      }
      return { data }
    })
    return true
  }

  onSaveSuccess() {
    // No implementation required as of now
  }

  onSaveFail() {
    // No implementation required as of now
  }

  _valueChange(fieldName, oldValue, dataDict) {
    if (this.serviceName === 'policies_and_computers') {
      const newValue = dataDict.data.collect_data_for.value
      const optionList = newValue.split(',')

      if (!optionList.includes('policies')) {
        this.util.setState(prevState => {
          const data = { ...prevState.data }
          data.collect_policy_details.disabled = true
          data.collect_policy_details.value = 0
          return { data }
        })
      } else {
        this.util.setState(prevState => {
          const data = { ...prevState.data }
          data.collect_policy_details.value = 0
          data.collect_policy_details.disabled = false
          return { data }
        })
      }
    }
  }

  _startDateChange(oldStartDate, dataDict) {
    var currentStartDate = dataDict.data.start_date.value
    if (
      (oldStartDate !== undefined ||
        oldStartDate !== '' ||
        oldStartDate !== null) &&
      oldStartDate !== currentStartDate
    ) {
      this.util.setState(prevState => {
        let data = { ...prevState.data }
        data.start_date.markdownMessage = {
          text: 'Changing this parameter may result in gaps or duplication in data collection',
          color: 'red',
          markdownType: 'text'
        }
        return { data }
      })
    }
  }
}
export default Hook
