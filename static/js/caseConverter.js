/**
 * Case Conversion Utilities
 * Provides conversion between snake_case and camelCase for API boundary
 */

/**
 * Convert snake_case string to camelCase
 * @param {string} str - Snake case string
 * @returns {string} Camel case string
 */
function snakeToCamel(str) {
    if (typeof str !== 'string') return str;
    return str.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
}

/**
 * Convert camelCase string to snake_case
 * @param {string} str - Camel case string
 * @returns {string} Snake case string
 */
function camelToSnake(str) {
    if (typeof str !== 'string') return str;
    return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}

/**
 * Recursively convert object keys from snake_case to camelCase
 * @param {any} obj - Object to convert
 * @returns {any} Converted object
 */
function keysToCamel(obj) {
    if (obj == null) return obj;
    if (Array.isArray(obj)) return obj.map(keysToCamel);
    if (typeof obj === 'object' && obj.constructor === Object) {
        return Object.fromEntries(
            Object.entries(obj).map(([key, value]) => [snakeToCamel(key), keysToCamel(value)])
        );
    }
    return obj;
}

/**
 * Recursively convert object keys from camelCase to snake_case
 * @param {any} obj - Object to convert
 * @returns {any} Converted object
 */
function keysToSnake(obj) {
    if (obj == null) return obj;
    if (Array.isArray(obj)) return obj.map(keysToSnake);
    if (typeof obj === 'object' && obj.constructor === Object) {
        return Object.fromEntries(
            Object.entries(obj).map(([key, value]) => [camelToSnake(key), keysToSnake(value)])
        );
    }
    return obj;
}
