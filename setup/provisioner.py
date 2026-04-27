import subprocess
import sys
import json
from pathlib import Path

# Central registry file to keep track of assigned ports
REGISTRY_FILE = Path("/home/clairify/claires/setup/port_registry.json")
START_PORT = 18796  # The starting port for your first bot

def load_registry():
    """Loads the port registry from the JSON file."""
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_registry(registry_data):
    """Saves the updated port registry to the JSON file."""
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry_data, f, indent=4)

def get_next_available_port(registry):
    """Determines the next available port based on the registry."""
    if not registry:
        # If the registry is empty, return the starting port
        return str(START_PORT)
    
    # Extract all currently used ports, convert to integers, and find the max
    used_ports = [int(p) for p in registry.values()]
    next_port = max(used_ports) + 1
    return str(next_port)

def create_bot(user_name, tg_token, tg_id):
    # 1. Bot Existence Check (Still our first line of defense)
    agent_dir = Path(f"/home/clairify/claires/agents/{user_name}")
    if agent_dir.exists() and agent_dir.is_dir():
        return {
            "status": "exists", 
            "message": f"System Notice: A bot named 'claire-{user_name}' already exists. Inform the user that it already exists and politely ask them to please create the bot with another name."
        }

    # 2. Automatically Determine the Next Port
    registry = load_registry()
    assigned_port = get_next_available_port(registry)

    # 3. Proceed with Creation
    script_path = "/home/clairify/claires/setup/spawn_claire.sh"
    try:
        # Run your bash script, passing the dynamically assigned port
        result = subprocess.run(
            ["sudo", script_path, user_name, assigned_port, tg_token, str(tg_id)],
            capture_output=True, text=True, check=True
        )
        
        # 4. Save the new bot and its auto-assigned port to the registry
        registry[user_name] = assigned_port
        save_registry(registry)

        # Inform Openclaire of the success and the specific port used
        return {
            "status": "success", 
            "message": f"System Notice: Successfully created claire-{user_name} and automatically assigned port {assigned_port}.",
            "output": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr}

if __name__ == "__main__":
    # Load args from Openclaire
    args = json.loads(sys.argv[1])
    
    # Notice that 'port' is completely removed from the incoming arguments
    response = create_bot(args['user_name'], args['tg_token'], args['tg_id'])
    print(json.dumps(response))
