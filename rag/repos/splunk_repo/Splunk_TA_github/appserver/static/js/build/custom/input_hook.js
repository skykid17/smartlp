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
             * @param {String} serviceName - Service name
             * @param {object} state - Initial state of the form
             * @param {String} mode - Form mode. Can be edit, create or clone
             * @param {object} util - Object containing utility methods
             *      {
                        setState,
                        setErrorMsg
                    }
            */
  constructor(globalConfig, serviceName, state, mode, util) {
    this.globalConfig = globalConfig
    this.serviceName = serviceName
    this.state = state
    this.mode = mode
    this.util = util
  }

  onRender(){
    this.util.setState((prevState) =>{
      const data = {
        ...prevState.data
      }

        if (this.serviceName === "github_alerts_input"){
            if (data.alert_type.value == null) {
              data.alert_type.display = true
              data.alert_type.value = 'code_scanning_alerts'
              if (data.account_type.value === 'orgs'){
                data.severity.display = true
              }else{
                data.severity.display = false
              }
              data.dependabot_ecosystem.display = false
              data.dependabot_scope.display = false
              data.dependabot_severity.display  = false
              data.dependabot_state.display  = false
              data.secret_scanning_resolution.display  = false
              data.secret_scanning_validity.display  = false
              data.secret_scanning_state.display = false
            }
            if(data.account_type.value === "enterprises"){
               data.severity.display = false
            }

        }

      return {
        data
      }
    })
  }

  _updateMultipleSelectField(field, data) {
      // Get the value from the data object
    let fieldValue = data[field].value;
    let valueArray = fieldValue.split(',');

    // Check if there are more than one value and remove 'all' if present
    if (valueArray.length > 1) {
        valueArray = valueArray.filter(item => item !== 'all');
    }

    data[field].value = valueArray.join(',');
  }

  onChange(field, value, dataDict) {
    // Change the field according to account type
    this.util.setState((prevState) => {
      const data = {
        ...prevState.data
      }
      if (this.serviceName === "github_audit_input") {
        if (field === 'start_date' && this.mode === 'edit') {
          var oldStartDate = this.state.data.start_date.value
          this._startDateChange(oldStartDate, dataDict)
        }
      }
      if (this.serviceName === "github_alerts_input"
      && (field === 'alert_type' || field === 'account_type')){
        if (field === 'alert_type' && value === 'code_scanning_alerts'
           && data.account_type.value === 'orgs') {
            data.severity.display = true
        }else if(field === 'account_type' && value === 'orgs'
           && data.alert_type.value === 'code_scanning_alerts'){
            data.severity.display = true
        }else{
            data.severity.display = false
        }
      }
      if (this.mode === "clone" && this.serviceName === "github_alerts_input"
         && field === "alert_type" && value === "dependabot_alerts") {
         data.dependabot_ecosystem.value = "all"
         data.dependabot_severity.value = "all"
         data.dependabot_scope.value = "all"
         data.dependabot_state.value = "all"
      }
      if (this.mode === "clone" && this.serviceName === "github_alerts_input"
         && field === "alert_type" && value === "code_scanning_alerts") {
         data.severity.value = "all"
         data.state.value = "all"
      }
      if (this.mode === "clone" && this.serviceName === "github_alerts_input"
         && field === "alert_type" && value === "secret_scanning_alerts") {
         data.secret_scanning_resolution.value = "all"
         data.secret_scanning_validity.value = "all"
         data.secret_scanning_state.value = "open"
      }

      //check if multiSelect field does have any 'all' value selected
      if (
        field === 'dependabot_severity' ||
        field === 'dependabot_state' ||
        field === 'dependabot_ecosystem' ||
        field === 'secret_scanning_resolution' ||
        field === 'secret_scanning_validity'
      ) {
        this._updateMultipleSelectField(field, data)
      }

      return {
        data
      }
    })
  }

  onEditLoad() {
    this.util.setState((prevState) => {
      const data = {
        ...prevState.data
      }
      if (this.serviceName === "github_audit_input") {
        data.use_existing_checkpoint.display = true
        data.use_existing_checkpoint.value = 'yes'
        data.use_existing_checkpoint.markdownMessage = {
          text: 'A Checkpoint for this input already exists. Selecting `No` will reset the data collection.',
          color: 'red',
          markdownType: 'text'
        }
        data.start_date.disabled = true
      }
      if (this.serviceName === "github_alerts_input"){
        if (data.alert_type.value == null) {
          data.alert_type.display = true
          data.alert_type.value = 'code_scanning_alerts'
          if (data.account_type.value === 'orgs'){
            data.severity.display = true
          }else{
            data.severity.display = false
          }
          data.dependabot_ecosystem.display = false

          data.dependabot_scope.display = false
          data.dependabot_severity.display  = false
          data.dependabot_state.display  = false
          data.secret_scanning_resolution.display  = false
          data.secret_scanning_validity.display  = false
          data.secret_scanning_state.display = false
        }
        if(data.account_type.value === "enterprises"){
          data.severity.display = false
        }
      }

      return {
        data
      }
    })
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

export default InputHook
