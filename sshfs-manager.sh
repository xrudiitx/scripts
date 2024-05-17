#!/bin/bash

# Define SSHFS mount points
declare -A MOUNT_POINTS=(
    ["production:/tmp/a/1"]="/tmp/a/1"
    ["production:/tmp/a/2"]="/tmp/a/2"
    ["production:/tmp/a/3"]="/tmp/a/3"
    # Add more mount points as needed
)

LOG_FILE="/var/log/sshfs_mount.log"
RETRY_COUNT=3

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check if directory exists
check_directory_exists() {
    if [ ! -d "$1" ]; then
        log_message "Error: Directory $1 does not exist. Creating..."
        if ! mkdir -p "$1"; then
            log_message "Error: Failed to create directory $1"
            exit 1
        fi
    fi
}

# Function to check SSH connectivity
check_ssh_connectivity() {
    local source_dir=$1
    local host=$(echo "$source_dir" | cut -d':' -f1)
    log_message "Checking SSH connectivity to $host"
    if ! ssh -q -o BatchMode=yes -o ConnectTimeout=5 "$host" exit; then
        log_message "Error: Cannot establish SSH connection to $host"
        exit 1
    fi
}

# Function to mount SSHFS directories
mount_sshfs() {
    for source_dir in "${!MOUNT_POINTS[@]}"; do
        target_dir="${MOUNT_POINTS[$source_dir]}"
        check_directory_exists "$target_dir"
        check_ssh_connectivity "$source_dir"

        if ! mountpoint -q "$target_dir"; then
            log_message "Mounting $source_dir to $target_dir"
            local attempt=1
            while (( attempt <= RETRY_COUNT )); do
                if sshfs -o allow_other,default_permissions "$source_dir" "$target_dir"; then
                    log_message "Successfully mounted $source_dir to $target_dir on attempt $attempt"
                    break
                else
                    log_message "Error: Failed to mount $source_dir to $target_dir on attempt $attempt"
                    (( attempt++ ))
                    sleep 1
                fi
            done
            if (( attempt > RETRY_COUNT )); then
                log_message "Error: Exhausted all attempts to mount $source_dir to $target_dir"
            fi
        else
            log_message "Warning: $target_dir is already mounted"
            # Check if mount entry exists in /etc/fstab
            if ! grep -q "^$source_dir $target_dir fuse.sshfs" /etc/fstab; then
                log_message "Error: $target_dir is mounted but not defined in /etc/fstab"
                # Optionally, offer to add the entry to /etc/fstab
                read -p "Do you want to add $source_dir to /etc/fstab? [y/N]: " add_to_fstab
                if [[ $add_to_fstab =~ ^[Yy]$ ]]; then
                    echo "$source_dir $target_dir fuse.sshfs _netdev,allow_other,default_permissions 0 0" | sudo tee -a /etc/fstab
                    log_message "$source_dir added to /etc/fstab"
                fi
            fi
        fi
    done
}

# Function to unmount SSHFS directories
unmount_sshfs() {
    for target_dir in "${MOUNT_POINTS[@]}"; do
        if mountpoint -q "$target_dir"; then
            log_message "Unmounting $target_dir"
            if ! sudo umount "$target_dir"; then
                log_message "Error: Failed to unmount $target_dir"
            else
                log_message "Successfully unmounted $target_dir"
            fi
        fi
    done
}

# Function to check SSHFS mount status
check_mount_status() {
    local error_count=0
    for source_dir in "${!MOUNT_POINTS[@]}"; do
        target_dir="${MOUNT_POINTS[$source_dir]}"
        if ! mountpoint -q "$target_dir"; then
            log_message "Error: Mount failed - $source_dir is not mounted to $target_dir"
            ((error_count++))
        fi
    done
    if [ "$error_count" -eq 0 ]; then
        log_message "All mount points are mounted successfully."
    else
        log_message "Error: Some mount points failed"
    fi
}

# Function to show defined mount points
show_mount_points() {
    echo "Defined SSHFS mount points:"
    for source_dir in "${!MOUNT_POINTS[@]}"; do
        echo "  $source_dir -> ${MOUNT_POINTS[$source_dir]}"
    done
    echo ""
}

# Function to check disk space
check_disk_space() {
    for target_dir in "${MOUNT_POINTS[@]}"; do
        if mountpoint -q "$target_dir"; then
            df -h "$target_dir" | tee -a "$LOG_FILE"
        fi
    done
}

# Function to check fstab integrity
check_fstab_integrity() {
    log_message "Checking /etc/fstab integrity"
    if ! grep -q '^\S' /etc/fstab; then
        log_message "Warning: /etc/fstab has formatting issues"
    fi
}

# Help function
show_help() {
    echo "Usage: $0 [mount|umount|status|check|help]"
    echo "Manage SSHFS directories defined in the script."
    echo ""
    echo "Options:"
    echo "  mount     Mount SSHFS directories"
    echo "  umount    Unmount SSHFS directories"
    echo "  status    Check the status of SSHFS mounts"
    echo "  check     Check disk space and fstab integrity"
    echo "  help      Show this help message"
    echo ""
    show_mount_points
}

# Main function
main() {
    case "$1" in
        mount)
            mount_sshfs
            check_mount_status
            ;;
        umount)
            unmount_sshfs
            ;;
        status)
            check_mount_status
            ;;
        check)
            check_disk_space
            check_fstab_integrity
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Call the main function with argument
main "$@"
