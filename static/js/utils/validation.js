/**
 * Form Validation Utility Module
 * Provides shared validation helpers for settings forms
 */

class ValidationManager {
    constructor() {
        this.validators = {
            required: (value) => ({
                valid: value !== null && value !== undefined && value !== '',
                message: 'This field is required'
            }),
            number: (value) => ({
                valid: !isNaN(Number(value)),
                message: 'Must be a valid number'
            }),
            positiveNumber: (value) => ({
                valid: !isNaN(Number(value)) && Number(value) > 0,
                message: 'Must be a positive number'
            }),
            numberRange: (value, min, max) => ({
                valid: !isNaN(Number(value)) && Number(value) >= min && Number(value) <= max,
                message: `Must be between ${min} and ${max}`
            }),
            url: (value) => ({
                valid: !value || /^https?:\/\/.+$/.test(value),
                message: 'Must be a valid URL (http:// or https://)'
            }),
            email: (value) => ({
                valid: !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
                message: 'Must be a valid email address'
            }),
            minLength: (value, length) => ({
                valid: value && value.length >= length,
                message: `Must be at least ${length} characters`
            }),
            maxLength: (value, length) => ({
                valid: !value || value.length <= length,
                message: `Must be no more than ${length} characters`
            })
        };
    }

    /**
     * Validate a single field
     * @param {string} value - The field value
     * @param {Array} rules - Array of validation rules
     * @returns {Object} - { valid: boolean, errors: string[] }
     */
    validateField(value, rules) {
        const errors = [];

        for (const rule of rules) {
            const [validatorName, ...args] = Array.isArray(rule) ? rule : [rule];
            const validator = this.validators[validatorName];

            if (!validator) {
                console.warn(`Unknown validator: ${validatorName}`);
                continue;
            }

            const result = validator(value, ...args);
            if (!result.valid) {
                errors.push(result.message);
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Validate settings form before submission
     * @returns {Object} - { valid: boolean, errors: string[] }
     */
    validateSettingsForm() {
        const errors = [];

        // Global settings validation
        const ingestFrequency = document.getElementById('ingestFrequency')?.value;
        const frequencyResult = this.validateField(ingestFrequency, [
            ['required'],
            ['positiveNumber']
        ]);
        if (!frequencyResult.valid) {
            errors.push(`Ingest Frequency: ${frequencyResult.errors.join(', ')}`);
        }

        const similarityThreshold = document.getElementById('similarityThreshold')?.value;
        const thresholdResult = this.validateField(similarityThreshold, [
            ['required'],
            ['numberRange', 0, 1]
        ]);
        if (!thresholdResult.valid) {
            errors.push(`Similarity Threshold: ${thresholdResult.errors.join(', ')}`);
        }

        const fixCount = document.getElementById('fixCount')?.value;
        const fixCountResult = this.validateField(fixCount, [
            ['required'],
            ['positiveNumber']
        ]);
        if (!fixCountResult.valid) {
            errors.push(`Fix Count: ${fixCountResult.errors.join(', ')}`);
        }

        // SIEM settings validation (only for selected SIEM)
        const siemSelect = document.getElementById('siemSelect')?.value;
        if (siemSelect) {
            const siemId = siemSelect.toLowerCase();

            if (siemId === 'elastic') {
                const elasticHost = document.getElementById('elasticHost')?.value;
                const hostResult = this.validateField(elasticHost, [['required']]);
                if (!hostResult.valid) {
                    errors.push('Elastic Host is required');
                }

                const elasticApiKey = document.getElementById('elasticApiKey')?.value;
                const apiKeyResult = this.validateField(elasticApiKey, [['required']]);
                if (!apiKeyResult.valid) {
                    errors.push('Elastic API Key is required');
                }

                const elasticKibanaUrl = document.getElementById('elasticKibanaUrl')?.value;
                const urlResult = this.validateField(elasticKibanaUrl, [['url']]);
                if (!urlResult.valid) {
                    errors.push('Elastic Kibana URL must be a valid URL');
                }
            } else if (siemId === 'splunk') {
                const splunkHost = document.getElementById('splunkHost')?.value;
                const hostResult = this.validateField(splunkHost, [['required']]);
                if (!hostResult.valid) {
                    errors.push('Splunk Host is required');
                }

                const splunkPort = document.getElementById('splunkPort')?.value;
                const portResult = this.validateField(splunkPort, [
                    ['required'],
                    ['numberRange', 1, 65535]
                ]);
                if (!portResult.valid) {
                    errors.push('Splunk Port must be between 1 and 65535');
                }
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Show validation errors as toasts
     * @param {string[]} errors - Array of error messages
     */
    showValidationErrors(errors) {
        if (typeof window.showToast === 'function') {
            errors.forEach(error => {
                window.showToast(error, 'error');
            });
        } else {
            console.error('Validation errors:', errors);
        }
    }

    /**
     * Mark a field as invalid with visual feedback
     * @param {HTMLElement} field - The input field
     * @param {string} errorMessage - The error message to display
     */
    markFieldInvalid(field, errorMessage) {
        if (!field) return;

        // Add error styling
        field.classList.add('border-red-500', 'focus:ring-red-500');
        field.classList.remove('border-gray-300', 'dark:border-gray-600', 'focus:ring-blue-500');

        // Remove existing error message if any
        const existingError = field.parentElement.querySelector('.field-error-message');
        if (existingError) {
            existingError.remove();
        }

        // Add error message
        const errorEl = document.createElement('p');
        errorEl.className = 'mt-1 text-sm text-red-600 dark:text-red-400 field-error-message';
        errorEl.textContent = errorMessage;
        field.parentElement.appendChild(errorEl);

        // Remove error styling on next input
        const cleanup = () => {
            field.classList.remove('border-red-500', 'focus:ring-red-500');
            field.classList.add('border-gray-300', 'dark:border-gray-600', 'focus:ring-blue-500');
            const errEl = field.parentElement.querySelector('.field-error-message');
            if (errEl) errEl.remove();
            field.removeEventListener('input', cleanup);
        };
        field.addEventListener('input', cleanup);
    }

    /**
     * Clear validation errors from a field
     * @param {HTMLElement} field - The input field
     */
    clearFieldError(field) {
        if (!field) return;

        field.classList.remove('border-red-500', 'focus:ring-red-500');
        field.classList.add('border-gray-300', 'dark:border-gray-600', 'focus:ring-blue-500');

        const existingError = field.parentElement.querySelector('.field-error-message');
        if (existingError) {
            existingError.remove();
        }
    }
}

// Create singleton instance
const validationManager = new ValidationManager();

// Export for ES6 modules
export default validationManager;

// Also attach to window for backward compatibility
if (typeof window !== 'undefined') {
    window.validationManager = validationManager;
    window.validateSettingsForm = () => validationManager.validateSettingsForm();
}
