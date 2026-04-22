#!/bin/bash
#Uage: sudo ./spawn_claire.sh [user_name] [port] [tg_token] [tg_id]
USER_NAME=$1
PORT=$2
TG_TOKEN=$3
TG_ID=$4

BASE_PATH="/home/clairify/claires/agents/$USER_NAME"
TEMPLATE_PATH="/home/clairify/claires/template/openclaw.json"

# 1. Create the user directories if they don't exist
mkdir -p $BASE_PATH/{openclaw,pcds,secrets,workspace}

# 2. Patch the template and move it to the user's openclaw folder
# Note: We use the variables passed to the script
sed -e "s/{{TG_BOT_TOKEN}}/$TG_TOKEN/g" \
    -e "s/{{TG_ADMIN_ID}}/$TG_ID/g" \
    -e "s/{{GATEWAY_TOKEN}}/randy-claire-2026/g" \
    -e "s/{{PRIMARY_MODEL}}/qwen3.5:9b/g" \
    $TEMPLATE_PATH > $BASE_PATH/openclaw/openclaw.json

# 3. Permission Fix (The "No Headache" rule)
chmod -R 777 $BASE_PATH

# 4. Launch Docker
docker run -d \
  --name "claire-$USER_NAME" \
  -p "$PORT:18790" \
  -v "$BASE_PATH/openclaw:/home/claire/.openclaw" \
  -v "$BASE_PATH/pcds:/home/claire/pcds" \
  -v "$BASE_PATH/workspace:/home/claire/.openclaw/workspace" \
  clairify/claire:latest
