#!/bin/sh

# Shutdown service
echo "Shuttind down Plex service..."
kubectl exec -n plex pms-0 -- /plex_service.sh -d

# Perform restore
echo "Using latest backup..."
kubectl exec -n plex pms-0 -- sh -c "tar zxvf /data/configs/plex/plex_backup_latest.tar.gz -C /config"

# Bring up service
echo "Starting Plex service..."
kubectl exec -n plex pms-0 -- /plex_service.sh -u