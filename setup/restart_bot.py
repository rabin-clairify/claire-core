import subprocess
import sys
import json

def get_container_status(container_name):
    try:
        result = subprocess.run(
            ["sudo", "docker", "inspect", "-f", "{{.State.Status}}", container_name],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "not_found"

def restart_bot(raw_user_name):
    # Normalize input
    if raw_user_name.startswith("claire-"):
        user_name = raw_user_name.replace("claire-", "", 1)
    else:
        user_name = raw_user_name

    container_name = f"claire-{user_name}"
    status = get_container_status(container_name)

    if status == "not_found":
        return {
            "status": "error",
            "message": f"System Notice: Bot '{container_name}' does not exist. It cannot be restarted."
        }

    try:
        # Restart the container (works on both running and stopped containers)
        subprocess.run(["sudo", "docker", "restart", container_name], capture_output=True, check=True)
        return {
            "status": "success",
            "message": f"System Notice: Successfully restarted the bot '{container_name}'."
        }
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Failed to restart container: {e.stderr}"}

if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    response = restart_bot(args['user_name'])
    print(json.dumps(response))
