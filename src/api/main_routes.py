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
        """Main dashboard page."""
        return render_template("dashboard.html", page_title="SmartSOC")