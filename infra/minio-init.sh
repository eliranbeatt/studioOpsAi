#!/bin/bash

# MinIO initialization script for StudioOps AI
# This script sets up buckets and policies for document storage

set -e

echo "Starting MinIO initialization..."

# Wait for MinIO to be ready
echo "Waiting for MinIO server to be ready..."
until curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; do
    echo "MinIO not ready yet, waiting..."
    sleep 2
done

echo "MinIO server is ready, configuring..."

# Set up MinIO client alias
mc alias set local http://localhost:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}

# Create buckets for different purposes
echo "Creating buckets..."

# Documents bucket - for processed and final documents
mc mb local/documents --ignore-existing
echo "Created documents bucket"

# Uploads bucket - for temporary file uploads
mc mb local/uploads --ignore-existing
echo "Created uploads bucket"

# Exports bucket - for generated PDFs and exports
mc mb local/exports --ignore-existing
echo "Created exports bucket"

# Temp bucket - for temporary processing files
mc mb local/temp --ignore-existing
echo "Created temp bucket"

# Set bucket policies
echo "Setting bucket policies..."

# Documents bucket - private by default
mc anonymous set none local/documents
echo "Set documents bucket to private"

# Uploads bucket - allow uploads for authenticated users
mc anonymous set upload local/uploads
echo "Set uploads bucket to allow uploads"

# Exports bucket - allow downloads for generated documents
mc anonymous set download local/exports
echo "Set exports bucket to allow downloads"

# Temp bucket - private for processing
mc anonymous set none local/temp
echo "Set temp bucket to private"

# Create lifecycle policies for temp bucket (auto-cleanup after 7 days)
cat > /tmp/temp-lifecycle.json << EOF
{
    "Rules": [
        {
            "ID": "TempCleanup",
            "Status": "Enabled",
            "Expiration": {
                "Days": 7
            }
        }
    ]
}
EOF

mc ilm import local/temp < /tmp/temp-lifecycle.json
echo "Set lifecycle policy for temp bucket (7-day cleanup)"

# Set versioning for documents bucket
mc version enable local/documents
echo "Enabled versioning for documents bucket"

# Create notification configuration for document processing
# This would be used to trigger processing when files are uploaded
cat > /tmp/notification.json << EOF
{
    "CloudWatchConfigurations": null,
    "LambdaConfigurations": null,
    "QueueConfigurations": null,
    "TopicConfigurations": null
}
EOF

echo "MinIO initialization completed successfully!"
echo "Available buckets:"
mc ls local/

echo "Bucket policies:"
echo "- documents: private (authenticated access only)"
echo "- uploads: upload allowed (for file uploads)"
echo "- exports: download allowed (for generated documents)"
echo "- temp: private (processing files, 7-day cleanup)"