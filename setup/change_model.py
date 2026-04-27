import json
import subprocess
import os
import argparse

# --- Configuration Paths ---
BASE_AGENTS_DIR = "/home/clairify/claires/agents" 
SUPPORTED_MODELS_PATH = "/home/clairify/claires/setup/supported_models.json"

def validate_model(provider, model_name):
    # Check the master supported_models.json database
    try:
        with open(SUPPORTED_MODELS_PATH, 'r') as f:
            supported_models = json.load(f)
        
        if provider not in supported_models or model_name not in supported_models[provider]:
            return False, f"🚫 Validation Failed: '{model_name}' is not an authorized {provider} model in supported_models.json."
    except Exception as e:
        return False, f"❌ Error reading {SUPPORTED_MODELS_PATH}: {str(e)}"

    # Extra Safety Check for Local Models (Ollama)
    if provider == "ollama":
        try:
            result = subprocess.run(["ollama", "ls"], capture_output=True, text=True, check=True)
            if model_name not in result.stdout:
                return False, f"⚠️ Validation Failed: '{model_name}' is approved, but not installed. Run 'ollama run {model_name}' first."
        except Exception as e:
            return False, f"❌ Error executing 'ollama ls'. Details: {str(e)}"
            
    return True, ""

def update_single_bot(bot_name, target, provider, model_name):
    json_path = os.path.join(BASE_AGENTS_DIR, bot_name, "openclaw", "openclaw.json")
    
    if not os.path.exists(json_path):
        return f"❌ Error: Could not find openclaw.json for bot '{bot_name}'"

    try:
        with open(json_path, 'r') as f:
            config = json.load(f)

        if provider == "ollama":
            if "ollama" not in config.get("models", {}).get("providers", {}):
                return f"❌ Error: Bot '{bot_name}' is missing the 'ollama' provider block."
            
            ollama_models_list = config["models"]["providers"]["ollama"].get("models", [])
            if not any(m.get("id") == model_name for m in ollama_models_list):
                ollama_models_list.append({
                    "id": model_name,
                    "name": f"{model_name.capitalize()} (Auto-Added Local)",
                    "api": "openai-completions",
                    "reasoning": False,
                    "input": ["text"],
                    "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
                    "contextWindow": 32768,
                    "maxTokens": 8192
                })
                config["models"]["providers"]["ollama"]["models"] = ollama_models_list

        primary_fallback_str = model_name if provider == "ollama" else f"{provider}/{model_name}"
        heartbeat_str = f"{provider}/{model_name}"
        full_agent_model_str = f"{provider}/{model_name}"

        targets_updated = []
        if target in ["primary", "all"]:
            config["agents"]["defaults"]["model"]["primary"] = primary_fallback_str
            targets_updated.append("Primary")
        if target in ["fallback", "all"]:
            config["agents"]["defaults"]["model"]["fallbacks"] = [primary_fallback_str]
            targets_updated.append("Fallback")
        if target in ["heartbeat", "all"]:
            if "heartbeat" not in config["agents"]["defaults"]:
                 config["agents"]["defaults"]["heartbeat"] = {"every": "1h", "lightContext": True}
            config["agents"]["defaults"]["heartbeat"]["model"] = heartbeat_str
            targets_updated.append("Heartbeat")

        if "models" not in config["agents"]["defaults"]:
            config["agents"]["defaults"]["models"] = {}
        if full_agent_model_str not in config["agents"]["defaults"]["models"]:
            config["agents"]["defaults"]["models"][full_agent_model_str] = {}

        with open(json_path, 'w') as f:
            json.dump(config, f, indent=2)

    except Exception as e:
        return f"❌ File Operation Failed for '{bot_name}': {str(e)}"

    try:
        container_name = f"claire-{bot_name}"
        subprocess.run(["docker", "restart", container_name], check=True, capture_output=True)
        return f"✅ '{bot_name}': Updated {', '.join(targets_updated)} to `{model_name}` and restarted."
    except Exception as e:
        return f"⚠️ '{bot_name}': JSON updated successfully, but failed to restart container. Details: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="OpenClaire Skill: Dynamically change bot models.")
    parser.add_argument("--bot", required=True, help="Name of the bot, or 'all' for every bot.")
    parser.add_argument("--target", required=True, choices=["primary", "fallback", "heartbeat", "all"])
    parser.add_argument("--provider", required=True, choices=["ollama", "xai", "anthropic", "openai", "google"])
    parser.add_argument("--model", required=True, help="Exact model name")
    
    args = parser.parse_args()
    
    # Run validation once for the model
    is_valid, msg = validate_model(args.provider, args.model)
    if not is_valid:
        print(msg)
        return

    # Determine which bots to update
    bots_to_update = []
    if args.bot.lower() == "all":
        try:
            for item in os.listdir(BASE_AGENTS_DIR):
                if os.path.isdir(os.path.join(BASE_AGENTS_DIR, item)):
                    if os.path.exists(os.path.join(BASE_AGENTS_DIR, item, "openclaw", "openclaw.json")):
                        bots_to_update.append(item)
        except Exception as e:
            print(f"❌ Error reading agents directory: {str(e)}")
            return
            
        if not bots_to_update:
            print(f"❌ Error: No valid bot folders found in {BASE_AGENTS_DIR}")
            return
    else:
        bots_to_update = [args.bot]

    # Process all selected bots
    feedback_lines = []
    for b in bots_to_update:
        feedback_lines.append(update_single_bot(b, args.target, args.provider, args.model))
        
    # Print combined feedback for OpenClaire to read
    print("\n".join(feedback_lines))

if __name__ == "__main__":
    main()
