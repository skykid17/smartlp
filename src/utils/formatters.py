"""
Data formatting and conversion utilities for SmartSOC.
"""

from typing import Dict, Any, Union
import nanoid


def snake_to_camel(snake_str: str) -> str:
    """Convert snake_case string to camelCase.
    
    Args:
        snake_str: String in snake_case format
        
    Returns:
        String in camelCase format
    """
    parts = snake_str.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


def convert_key_to_camel(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dictionary keys from snake_case to camelCase.
    
    Args:
        data: Dictionary with snake_case keys
        
    Returns:
        Dictionary with camelCase keys
    """
    return {snake_to_camel(key): value for key, value in data.items()}


def camel_to_snake(camel_str: str) -> str:
    """Convert camelCase string to snake_case.
    
    Args:
        camel_str: String in camelCase format
        
    Returns:
        String in snake_case format
    """
    result = []
    for i, char in enumerate(camel_str):
        if char.isupper() and i > 0:
            result.append('_')
        result.append(char.lower())
    return ''.join(result)


def convert_key_to_snake(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dictionary keys from camelCase to snake_case.
    
    Args:
        data: Dictionary with camelCase keys
        
    Returns:
        Dictionary with snake_case keys
    """
    return {camel_to_snake(key): value for key, value in data.items()}


def generate_alphanumeric_id(size: int = 8) -> str:
    """Generate alphanumeric ID.
    
    Args:
        size: Length of ID to generate
        
    Returns:
        Random alphanumeric string
    """
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return nanoid.generate(alphabet=alphabet, size=size)


def sanitize_string(text: str) -> str:
    """Sanitize string for safe processing.
    
    Args:
        text: Input string
        
    Returns:
        Sanitized string
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove null bytes and control characters
    sanitized = text.replace('\x00', '').replace('\r', '').replace('\n', ' ')
    
    # Limit length to prevent memory issues
    if len(sanitized) > 10000:
        sanitized = sanitized[:10000] + "..."
    
    return sanitized.strip()


def safe_dict_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary with nested key support.
    
    Args:
        data: Dictionary to search
        key: Key to search for (supports dot notation for nested keys)
        default: Default value if key not found
        
    Returns:
        Value from dictionary or default
    """
    if not isinstance(data, dict):
        return default
    
    if '.' not in key:
        return data.get(key, default)
    
    keys = key.split('.')
    current = data
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries safely.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result


def validate_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if not isinstance(text, str):
        text = str(text)
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix