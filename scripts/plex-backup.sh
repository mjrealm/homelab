#!/bin/sh

# Shutdown service
echo "Shuttind down Plex service..."
kubectl exec -n plex pms-0 -- /plex_service.sh -d

# Performing backup
current_date=$(date +"%m-%d-%Y_%H-%M")
echo "Today's date is: $current_date"

echo "Current backups..."
kubectl exec -n plex pms-0 -- ls -al /data/configs/plex
sleep 10

echo "Starting backup..."
kubectl exec -n plex pms-0 -- sh -c "cd /config/ && tar czvf /data/configs/plex/plex_backup_$current_date.tar.gz Library/"

# Using symlink
echo "Creating latest symlink..."
kubectl exec -n plex pms-0 -- ln -sf /data/configs/plex/plex_backup_$current_date.tar.gz /data/configs/plex/plex_backup_latest.tar.gz

# Bring up service
echo "Starting Plex service..."
kubectl exec -n plex pms-0 -- /plex_service.sh -u