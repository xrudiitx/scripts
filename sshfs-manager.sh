#!/bin/bash

# Define SSHFS mount points
declare -A MOUNT_POINTS=(
    ["production:/tmp/a/1"]="/tmp/a/1"
    ["production:/tmp/a/2"]="/tmp/a/2"
    ["production:/tmp/a/3"]="/tmp/a/3"
    # Add more mount points as needed
)

# Function to mount SSHFS directories
mount_sshfs() {
    for source_dir in "${!MOUNT_POINTS[@]}"; do
        target_dir="${MOUNT_POINTS[$source_dir]}"
        if ! mountpoint -q "$target_dir"; then
            echo "Mounting $source_dir to $target_dir"
            if ! sshfs -o allow_other,default_permissions "$source_dir" "$target_dir"; then
                echo "Error: Failed to mount $source_dir to $target_dir"
            fi
        else
            echo "Warning: $target_dir is already mounted"
            # Check if mount entry exists in /etc/fstab
            if ! grep -q "^$source_dir $target_dir fuse.sshfs" /etc/fstab; then
                echo "Error: $target_dir is mounted but not defined in /etc/fstab"
            fi
        fi
    done
}

# Function to unmount SSHFS directories
unmount_sshfs() {
    for target_dir in "${MOUNT_POINTS[@]}"; do
        if mountpoint -q "$target_dir"; then
            echo "Unmounting $target_dir"
            if ! sudo umount "$target_dir"; then
                echo "Error: Failed to unmount $target_dir"
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
            echo "Error: Mount failed - $source_dir is not mounted to $target_dir"
            ((error_count++))
        fi
    done
    if [ "$error_count" -eq 0 ]; then
        echo "All mount points are mounted successfully."
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

# Help function
show_help() {
    echo "Usage: $0 [mount|umount]"
    echo "Mount or unmount SSHFS directories defined in the script."
    echo ""
    echo "Options:"
    echo "  mount     Mount SSHFS directories"
    echo "  umount    Unmount SSHFS directories"
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
        *)
            show_help
            ;;
    esac
}

# Call the main function with argument
main "$@"
