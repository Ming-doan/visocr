#!/bin/sh
set -e

echo "🚀 Starting MinIO initialization..."

# Install dependencies inside container (only once at startup)
if ! command -v jq >/dev/null 2>&1; then
    echo "📦 Installing jq and curl..."
    apk add --no-cache jq curl ca-certificates
fi

# Download MinIO client if not already available
if [ ! -f /usr/local/bin/mc ]; then
    echo "⬇️ Downloading MinIO client (mc)..."
    curl -s -o /usr/local/bin/mc https://dl.min.io/client/mc/release/linux-amd64/mc
    chmod +x /usr/local/bin/mc
fi

# Wait for MinIO to be ready
echo "⏳ Waiting for MinIO service..."
until nc -z $MINIO_HOST $MINIO_PORT >/dev/null 2>&1; do
    sleep 2
    echo "   ...still waiting for $MINIO_HOST:$MINIO_PORT"
done
echo "✅ MinIO is ready!"

# Set alias
mc alias set myminio http://$MINIO_HOST:$MINIO_PORT "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

# Always ensure the base bucket exists
mc mb myminio/raw --ignore-existing
mc mb myminio/utils --ignore-existing

# Path to configs.json
CONFIG_FILE="/minio/configs.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found at $CONFIG_FILE"
    exit 1
fi

echo "📄 Reading $CONFIG_FILE..."
FOLDERS=$(jq -r '.models[].data_folder' "$CONFIG_FILE")

# Loop through and create buckets
for folder in $FOLDERS; do
    BUCKET_NAME=$(echo "$folder" | tr '[:upper:]' '[:lower:]')
    echo "🪣 Creating bucket: $BUCKET_NAME"
    mc mb "myminio/$BUCKET_NAME" --ignore-existing
    mc mb "myminio/$BUCKET_NAME-annotated" --ignore-existing
done

echo "✅ All buckets created successfully."
