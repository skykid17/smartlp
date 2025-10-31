"""
Main application routes for SmartSOC.
"""

from flask import Flask, render_template


def register_main_routes(app: Flask) -> None:
    """Register main application routes.
    
    Args:
        app: Flask application instance
    """
    
    @app.route("/")
    def dashboard():
        """Main dashboard page - now serves unified SmartLP interface."""
        # Get entries and statuses for dashboard section
        from services.smartlp import smartlp_service
        entries, total_entries = smartlp_service.get_entries(page=1, per_page=15)
        statuses = smartlp_service.get_all_statuses()

        return render_template(
            "smartlp.html",
            page_title="SmartLP",
            entries=entries,
            statuses=statuses,
            total_entries=total_entries,
        )