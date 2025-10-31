/**
 *
 * SPDX-FileCopyrightText: 2024 Splunk, Inc.
 * SPDX-License-Identifier: LicenseRef-Splunk-8-2021
 *
 */
class Hook {
  constructor (globalConfig, serviceName, state, mode, util) {
    this.globalConfig = globalConfig
    this.serviceName = serviceName
    this.state = state
    this.mode = mode
    this.util = util
  }

  onCreate () {
    // No implementation required as of now
  }

  onRender () {
    const inputName = this.state.data.name.value
    if (this.mode !== 'create') {
      if (inputName) {
        this.util.setState((prevState) => {
          const data = { ...prevState.data }
          data.url.disabled = true
          return { data }
        })
      }
    }
  }

  onSave () {
    // No implementation required as of now
    return true
  }

  onSaveSuccess () {
    // No implementation required as of now
  }

  onSaveFail () {
    // No implementation required as of now
  }
}
export default Hook
