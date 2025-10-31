"""
Generic utility functions for SmartSOC.
"""

import time
from datetime import date, datetime
from typing import List, Optional, Any


def convert_dates_to_datetime(data: Any) -> Any:
    """Recursively converts datetime.date objects to datetime.datetime objects.
    
    Args:
        data: Data structure that may contain date objects
        
    Returns:
        Data structure with date objects converted to datetime objects
    """
    if isinstance(data, dict):
        return {k: convert_dates_to_datetime(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_dates_to_datetime(item) for item in data]
    elif isinstance(data, date) and not isinstance(data, datetime):
        return datetime.combine(data, time.min)
    else:
        return data


def generate_pagination_links(current_page: int, total_pages: int, 
                            boundaries: int = 1, around: int = 2) -> List[Optional[int]]:
    """
    Generates a list of page numbers and ellipses for pagination display.

    Args:
        current_page: The current active page number
        total_pages: The total number of pages
        boundaries: How many page numbers to show at the beginning and end
        around: How many page numbers to show before and after the current page

    Returns:
        A list containing integers (page numbers) and None (ellipses)
    """
    links = []
    if total_pages <= 1:
        return links  # No pagination needed for 0 or 1 page

    # Ensure current_page is within valid range
    current_page = max(1, min(current_page, total_pages))

    # Calculate the page numbers to display
    pages_to_show = set()

    # Add boundary pages (start)
    pages_to_show.update(range(1, min(boundaries + 1, total_pages + 1)))

    # Add pages around the current page
    start_around = max(1, current_page - around)
    end_around = min(total_pages, current_page + around)
    pages_to_show.update(range(start_around, end_around + 1))

    # Add boundary pages (end)
    pages_to_show.update(range(max(1, total_pages - boundaries + 1), total_pages + 1))

    # Sort the page numbers and add ellipses
    last_page = 0
    sorted_pages = sorted(list(pages_to_show))

    for page_num in sorted_pages:
        if page_num > 0:  # Ensure valid page number
            # Add ellipsis if there's a gap
            if page_num > last_page + 1:
                links.append(None)  # None represents an ellipsis
            links.append(page_num)
            last_page = page_num

    return links