"""
Deployment API routes for SmartSOC.
"""

from flask import Flask, request, jsonify

from services.deployment import deployment_service
from services.settings import settings_service


def register_deployment_routes(app: Flask) -> None:
    """Register deployment routes.
    
    Args:
        app: Flask application instance
    """
    
    @app.route("/api/deploy", methods=['POST'])
    def deploy_to_ansible():
        """Deploy selected rules to Ansible."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"logger": "No data provided"}), 400
            
            ids = data.get("ids", [])
            deployment_type = data.get("type")
            
            if not ids or not deployment_type:
                return jsonify({"logger": "Missing IDs or type"}), 400
            
            # Get active SIEM
            active_siem = settings_service.get_active_siem()
            if not active_siem:
                return jsonify({"logger": "No active SIEM configured"}), 400
            
            # Perform deployment
            success, message = deployment_service.deploy_rules(
                ids, deployment_type, active_siem
            )
            
            if success:
                return jsonify({"logger": message}), 200
            else:
                return jsonify({"logger": message}), 500
                
        except Exception as e:
            return jsonify({"logger": f"Deployment failed: {str(e)}"}), 500