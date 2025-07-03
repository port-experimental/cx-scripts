#!/usr/bin/env python3
"""
Port Integration Refresh Script

This script triggers a refresh/resync of a Port integration using the PATCH API endpoint.
To trigger a resync without changing the mapping, we send a PATCH request with an empty body.

Dependencies to install:
pip install python-dotenv requests

Usage:
python port-integration-refresh.py <integration_identifier>
python port-integration-refresh.py --list 

Environment variables required:
- PORT_CLIENT_ID: Your Port client ID
- PORT_CLIENT_SECRET: Your Port client secret
"""

import argparse
import logging
import os
import sys
from typing import Optional

import dotenv
import requests

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Port API configuration
PORT_API_URL = "https://api.getport.io/v1"
PORT_CLIENT_ID = os.getenv("PORT_CLIENT_ID")
PORT_CLIENT_SECRET = os.getenv("PORT_CLIENT_SECRET")


class PortAPIClient:
    """Port API client for managing integrations"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.headers = {}
        
    def authenticate(self) -> bool:
        """Authenticate with Port API and get access token"""
        try:
            credentials = {
                "clientId": self.client_id,
                "clientSecret": self.client_secret
            }
            
            logger.info("Authenticating with Port API...")
            response = requests.post(
                f"{PORT_API_URL}/auth/access_token",
                json=credentials,
                timeout=30
            )
            response.raise_for_status()
            
            self.access_token = response.json()["accessToken"]
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
            logger.info("Successfully authenticated with Port API")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to authenticate with Port API: {e}")
            return False
        except KeyError:
            logger.error("Invalid response format from Port API authentication")
            return False
    
    def get_integrations(self) -> Optional[list]:
        """Get all integrations from Port"""
        try:
            logger.info("Fetching all integrations...")
            response = requests.get(
                f"{PORT_API_URL}/integration",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            # Handle the response structure: {"ok": True, "integrations": [...]}
            if isinstance(response_data, dict) and 'integrations' in response_data:
                integrations = response_data['integrations']
            else:
                integrations = response_data
                
            logger.info(f"Found {len(integrations)} integrations")
            return integrations
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch integrations: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Response status code: {e.response.status_code}")
                    logger.error(f"Response text: {e.response.text}")
            return None
    
    def get_integration_details(self, installation_id: str) -> Optional[dict]:
        """Get detailed information about a specific integration"""
        try:
            response = requests.get(
                f"{PORT_API_URL}/integration/{installation_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch integration details for {installation_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Response status code: {e.response.status_code}")
                    logger.error(f"Response text: {e.response.text}")
            return None
    
    def refresh_integration(self, integration_identifier: str) -> bool:
        """
        Trigger a refresh/resync of an integration
        
        Args:
            integration_identifier: The identifier of the integration to refresh
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Triggering refresh for integration: {integration_identifier}")
            
            # According to the API docs, send a PATCH request with empty body to trigger resync
            response = requests.patch(
                f"{PORT_API_URL}/integration/{integration_identifier}",
                headers=self.headers,
                json={},  # Empty body for simple resync
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"Successfully triggered refresh for integration: {integration_identifier}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh integration {integration_identifier}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Response status code: {e.response.status_code}")
                    logger.error(f"Response text: {e.response.text}")
            return False
    
    def list_integrations(self) -> bool:
        """List all available integrations"""
        integrations = self.get_integrations()
        if integrations is None:
            return False
            
        if not integrations:
            logger.info("No integrations found")
            return True
            
        logger.info("Available integrations:")
        for integration in integrations:
            if isinstance(integration, dict):
                installation_id = integration.get('installationId', 'N/A')
                identifier = integration.get('identifier', 'N/A')
                title = integration.get('title', identifier)  # Use identifier as fallback for title
                integration_type = integration.get('integrationType', integration.get('installationAppType', 'N/A'))
                installation_type = integration.get('installationType', 'N/A')
                
                logger.info(f"  - {installation_id} ({title}) - Type: {integration_type} ({installation_type})")
            else:
                logger.info(f"  - {integration}")
            
        return True


def validate_environment() -> bool:
    """Validate that required environment variables are set"""
    if not PORT_CLIENT_ID:
        logger.error("PORT_CLIENT_ID environment variable is required")
        return False
        
    if not PORT_CLIENT_SECRET:
        logger.error("PORT_CLIENT_SECRET environment variable is required")
        return False
        
    return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Trigger a refresh of a Port integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python port-integration-refresh.py --list                    # List all integrations
  python port-integration-refresh.py 68406724                  # Refresh integration with installation ID 68406724
        """
    )
    
    parser.add_argument(
        "integration_identifier",
        nargs="?",
        help="The installation ID of the integration to refresh (use --list to see available IDs)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available integrations"
    )
    
    args = parser.parse_args()
    
    # Validate environment variables
    if not validate_environment():
        sys.exit(1)
    
    # Create Port API client
    client = PortAPIClient(PORT_CLIENT_ID, PORT_CLIENT_SECRET)
    
    # Authenticate
    if not client.authenticate():
        sys.exit(1)
    
    # Handle list command
    if args.list:
        if not client.list_integrations():
            sys.exit(1)
        return
    
    # Validate integration identifier
    if not args.integration_identifier:
        logger.error("Integration identifier is required (or use --list to see available integrations)")
        parser.print_help()
        sys.exit(1)
    
    # Trigger integration refresh
    if client.refresh_integration(args.integration_identifier):
        logger.info("Integration refresh completed successfully")
    else:
        logger.error("Integration refresh failed")
        sys.exit(1)


if __name__ == "__main__":
    main() 