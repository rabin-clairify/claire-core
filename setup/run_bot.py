import subprocess
import sys
import json
from pathlib import Path

REGISTRY_FILE = Path("/home/clairify/claires/setup/port_registry.json")

def load_registry():
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    return {}

def get_container_status(container_name):
    try:
        result = subprocess.run(
            ["sudo", "docker", "inspect", "-f", "{{.State.Status}}", container_name],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "not_found"

def start_bot(raw_user_name):
    # --- NORMALIZATION STEP ---
    # If Openclaire passes "claire-rabin", strip it down to "rabin"
    if raw_user_name.startswith("claire-"):
        user_name = raw_user_name.replace("claire-", "", 1)
    else:
        user_name = raw_user_name
    # --------------------------

    agent_dir = Path(f"/home/clairify/claires/agents/{user_name}")
    container_name = f"claire-{user_name}"

    # 1. Check if the bot directory actually exists
    if not agent_dir.exists() or not agent_dir.is_dir():
        return {
            "status": "error",
            "message": f"System Notice: The bot '{container_name}' does not exist in the system. Please advise the user to create it first."
        }

    # 2. Check the Docker container status
    status = get_container_status(container_name)

    if status == "running":
        return {
            "status": "already_running",
            "message": f"System Notice: Bot '{container_name}' is already up and running."
        }
        
    elif status in ["exited", "created", "stopped"]:
        try:
            subprocess.run(["sudo", "docker", "start", container_name], capture_output=True, check=True)
            return {
                "status": "success",
                "message": f"System Notice: Successfully woke up and started the existing bot '{container_name}'."
            }
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Failed to start stopped container: {e.stderr}"}

    # 3. Container does not exist at all, so we run a fresh one
    registry = load_registry()
    if user_name not in registry:
        return {
            "status": "error",
            "message": f"System Notice: Critical error - no port assigned for '{container_name}' in the registry."
        }
    
    port = registry[user_name]
    base_path = str(agent_dir)

    docker_cmd = [
        "sudo", "docker", "run", "-d",
        "--name", container_name,
        "-p", f"{port}:18790",
       "--env-file", "/home/clairify/claires/setup/.env",
        "-v", f"{base_path}/openclaw:/home/claire/.openclaw",
        "-v", f"{base_path}/pcds:/home/claire/pcds",
        "-v", f"{base_path}/workspace:/home/claire/.openclaw/workspace",
        "clairify/claire:latest"
    ]

    try:
        subprocess.run(docker_cmd, capture_output=True, text=True, check=True)
        return {
            "status": "success",
            "message": f"System Notice: Successfully launched a fresh container for '{container_name}' on port {port}."
        }
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Failed to run new container: {e.stderr}"}

if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    response = start_bot(args['user_name'])
    print(json.dumps(response))
