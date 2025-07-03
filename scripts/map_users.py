"""
# GitHub User to Port User Mapping

This script maps GitHub user entities in Port to their corresponding general Port user entities.

## Description

The script performs the following actions:
1.  Fetches all entities from the `_user` blueprint in Port.
2.  Creates an in-memory lookup map where the key is the user's email (`identifier`) and the value is the user's Port entity `identifier`.
3.  Fetches all entities from the `githubUser` blueprint.
4.  For each `githubUser` entity, it checks if the `user` relation is already set.
5.  If the relation is not set, it uses the `email` property of the `githubUser` to find a match in the `_user` lookup map.
6.  If a match is found, it updates the `githubUser` entity to establish a relation to the corresponding `_user` entity.

## Prerequisites

- Python 3.8+
- Port API Credentials (Client ID and Client Secret)

## Setup

1.  **Save this script** as `map_users.py`.

2.  **Install dependencies:**
    ```bash
    pip install requests python-dotenv
    ```

3.  **Set environment variables:**
    Create a `.env` file in the same directory as the script and add your credentials:

    ```
    PORT_CLIENT_ID="your_client_id"
    PORT_CLIENT_SECRET="your_client_secret"
    ```

    You can also override the default blueprint identifiers in your `.env` file:
    ```
    GITHUB_USER_BLUEPRINT="your_github_user_blueprint"
    USER_BLUEPRINT="your_port_user_blueprint"
    ```

## Usage

Run the script from your terminal.

**To perform the actual mapping:**
```bash
python map_users.py
```

**To perform a dry run (recommended first):**
```bash
python map_users.py --dry-run
```
"""

import os
import sys
import requests
import argparse
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

PORT_API_URL = "https://api.getport.io/v1"
PORT_CLIENT_ID = os.getenv("PORT_CLIENT_ID")
PORT_CLIENT_SECRET = os.getenv("PORT_CLIENT_SECRET")
GITHUB_USER_BLUEPRINT = os.getenv("GITHUB_USER_BLUEPRINT", "githubUser")
USER_BLUEPRINT = os.getenv("USER_BLUEPRINT", "_user")

# --- Port API Client ---
class PortClient:
    def __init__(self):
        self.access_token = self._get_access_token()
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _get_access_token(self):
        credentials = {"clientId": PORT_CLIENT_ID, "clientSecret": PORT_CLIENT_SECRET}
        token_url = f"{PORT_API_URL}/auth/access_token"
        print("Authenticating with Port API...")
        try:
            response = requests.post(token_url, json=credentials)
            response.raise_for_status()
            print("Authentication successful.")
            return response.json().get("accessToken")
        except requests.exceptions.HTTPError as e:
            print(f"Error authenticating with Port: {e}")
            print(f"Response body: {e.response.text}")
            return None

    def get_all_entities(self, blueprint_identifier: str):
        url = f"{PORT_API_URL}/blueprints/{blueprint_identifier}/entities"
        print(f"Fetching all entities for blueprint: {blueprint_identifier}...")
        all_entities = []
        
        params = {'exclude_calculated_properties': 'true', 'include': ['properties', 'relations', 'identifier', 'title']}
        
        while url:
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                all_entities.extend(data.get("entities", []))
                url = data.get("nextPageUrl")
                params = {} # Only needed for the first request
            except requests.exceptions.HTTPError as e:
                print(f"Error fetching entities: {e}")
                print(f"Response body: {e.response.text}")
                return None

        print(f"Successfully fetched {len(all_entities)} entities for blueprint {blueprint_identifier}.")
        return all_entities

    def update_entity(self, blueprint_identifier: str, entity_identifier: str, properties: dict, relations: dict):
        url = f"{PORT_API_URL}/blueprints/{blueprint_identifier}/entities/{entity_identifier}"
        payload = {"properties": properties, "relations": relations}
        print(f"Updating entity {entity_identifier} in blueprint {blueprint_identifier}...")
        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            print(f"Successfully updated entity {entity_identifier}.")
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"Error updating entity {entity_identifier}: {e}")
            print(f"Response body: {e.response.text}")
            return None

# --- Mapping Logic ---
def run_mapping(dry_run=False):
    """
    Fetches users and maps them based on email.
    If dry_run is True, it only prints the actions that would be taken.
    """
    client = PortClient()
    if not client.access_token:
        print("Failed to authenticate with Port. Please check your credentials.")
        sys.exit(1)

    # 1. Fetch all _user entities and create a lookup map
    print("--- Step 1: Fetching Port users and building lookup map ---")
    port_users = client.get_all_entities(USER_BLUEPRINT)
    if port_users is None:
        print("Failed to fetch Port users. Aborting.")
        sys.exit(1)
    
    user_map = {user["identifier"].lower(): user["identifier"] for user in port_users}
    print(f"Built a map of {len(user_map)} Port users.")

    # 2. Fetch all githubUser entities
    print(f"\n--- Step 2: Fetching GitHub users from Port ---")
    github_users = client.get_all_entities(GITHUB_USER_BLUEPRINT)
    if github_users is None:
        print("Failed to fetch GitHub users. Aborting.")
        sys.exit(1)

    # 3. Iterate and map
    dry_run_prefix = "[DRY RUN] " if dry_run else ""
    print(f"\n--- Step 3: {dry_run_prefix}Mapping GitHub users to Port users ---")
    
    stats = {"mapped": 0, "already_mapped": 0, "unmatched": 0}

    for gh_user in github_users:
        gh_user_identifier = gh_user["identifier"]
        
        if gh_user.get("relations", {}).get("user"):
            print(f"Skipping {gh_user_identifier}: already mapped.")
            stats["already_mapped"] += 1
            continue

        email = gh_user.get("properties", {}).get("email")
        if not email:
            print(f"Skipping {gh_user_identifier}: no email property found.")
            stats["unmatched"] += 1
            continue

        email = email.lower()

        if email in user_map:
            port_user_identifier = user_map[email]
            stats["mapped"] += 1
            
            if dry_run:
                print(f"{dry_run_prefix}Match found: Would map GitHub user '{gh_user_identifier}' to Port user '{port_user_identifier}'")
            else:
                print(f"Found a match for {gh_user_identifier} ({email}) -> Port user {port_user_identifier}. Updating...")
                client.update_entity(
                    blueprint_identifier=GITHUB_USER_BLUEPRINT,
                    entity_identifier=gh_user_identifier,
                    properties={},
                    relations={"user": port_user_identifier}
                )
        else:
            print(f"{dry_run_prefix}No match: No Port user found for GitHub user '{gh_user_identifier}' with email '{email}'.")
            stats["unmatched"] += 1

    print(f"\n--- {dry_run_prefix}Mapping Process Summary ---")
    print(f"To be mapped / Mapped: {stats['mapped']}")
    print(f"Already mapped: {stats['already_mapped']}")
    print(f"Could not be matched: {stats['unmatched']}")
    print("---------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Map GitHub users to Port users.")
    parser.add_argument("--dry-run", action="store_true", help="Run the script in test mode without making actual changes.")
    args = parser.parse_args()

    if args.dry_run:
        print("Starting DRY RUN of GitHub to Port user mapping process...")
        run_mapping(dry_run=True)
        print("\nDry run finished. No data was changed in Port.")
    else:
        print("Starting GitHub to Port user mapping process...")
        run_mapping(dry_run=False)
        print("\nMapping process finished.") 