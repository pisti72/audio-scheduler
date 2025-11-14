#!/bin/bash
#
# Audio Scheduler - Service Installation Script
# This script automates the installation of the audio-scheduler as a systemd service
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running as root
check_root() {
    if [ "$INSTALL_TYPE" = "system" ] && [ "$EUID" -ne 0 ]; then
        print_error "System-level installation requires root privileges"
        echo "Please run with sudo: sudo $0 --system"
        exit 1
    fi
    
    if [ "$INSTALL_TYPE" = "user" ] && [ "$EUID" -eq 0 ]; then
        print_error "User-level installation should NOT be run with sudo"
        echo "Please run without sudo: $0 --user"
        exit 1
    fi
}

# Detect audio system
detect_audio_system() {
    print_header "Detecting Audio System"
    
    if pgrep -x "pipewire" > /dev/null; then
        AUDIO_SYSTEM="pipewire"
        print_success "Detected PipeWire"
        AUDIO_AFTER="pipewire.service"
    elif pgrep -x "pulseaudio" > /dev/null; then
        AUDIO_SYSTEM="pulseaudio"
        print_success "Detected PulseAudio"
        AUDIO_AFTER="pulseaudio.service"
    else
        AUDIO_SYSTEM="unknown"
        print_warning "No PipeWire or PulseAudio detected"
        print_warning "Audio playback may not work correctly"
        AUDIO_AFTER="sound.target"
    fi
}

# Get user ID for runtime directory
get_user_id() {
    if [ "$INSTALL_TYPE" = "user" ]; then
        USER_ID=$(id -u)
        INSTALL_USER="$USER"
    else
        # For system installation, ask which user to run as
        read -p "Enter the username to run the service as [$SUDO_USER]: " SERVICE_USER
        SERVICE_USER="${SERVICE_USER:-$SUDO_USER}"
        USER_ID=$(id -u "$SERVICE_USER")
        INSTALL_USER="$SERVICE_USER"
    fi
    print_info "Service will run as user: $INSTALL_USER (UID: $USER_ID)"
}

# Create virtual environment if it doesn't exist
setup_venv() {
    print_header "Setting Up Virtual Environment"
    
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    print_info "Installing/updating dependencies..."
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
    deactivate
    print_success "Dependencies installed"
}

# Create user-level systemd service
create_user_service() {
    print_header "Creating User-Level Systemd Service"
    
    SERVICE_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SERVICE_DIR"
    
    cat > "$SERVICE_DIR/audio-scheduler.service" << EOF
[Unit]
Description=Audio Scheduler Service (User Mode)
After=network.target sound.target $AUDIO_AFTER

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR

# Environment variables for audio access
Environment="PULSE_SERVER=unix:/run/user/%U/pulse/native"
Environment="XDG_RUNTIME_DIR=/run/user/%U"

# Use bash to run the gunicorn command
# IMPORTANT: -w 1 (single worker) is critical to prevent duplicate schedulers
ExecStart=/bin/bash -c 'source venv/bin/activate && exec gunicorn \\
    -w 1 \\
    -b 0.0.0.0:5000 \\
    --timeout 120 \\
    --log-level info \\
    --access-logfile logs/gunicorn_access.log \\
    --error-logfile logs/gunicorn_error.log \\
    --capture-output \\
    wsgi:app'

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=audio-scheduler

[Install]
WantedBy=default.target
EOF

    print_success "Service file created at: $SERVICE_DIR/audio-scheduler.service"
}

# Create system-level systemd service
create_system_service() {
    print_header "Creating System-Level Systemd Service"
    
    SERVICE_DIR="/etc/systemd/system"
    
    cat > "$SERVICE_DIR/audio-scheduler.service" << EOF
[Unit]
Description=Audio Scheduler Service
After=network.target sound.target $AUDIO_AFTER

[Service]
Type=simple
User=$INSTALL_USER
Group=$INSTALL_USER
WorkingDirectory=$SCRIPT_DIR

# Environment variables for audio access
Environment="PULSE_SERVER=unix:/run/user/$USER_ID/pulse/native"
Environment="XDG_RUNTIME_DIR=/run/user/$USER_ID"

# Use bash to run the gunicorn command
# IMPORTANT: -w 1 (single worker) is critical to prevent duplicate schedulers
ExecStart=/bin/bash -c 'source venv/bin/activate && exec gunicorn \\
    -w 1 \\
    -b 0.0.0.0:5000 \\
    --timeout 120 \\
    --log-level info \\
    --access-logfile logs/gunicorn_access.log \\
    --error-logfile logs/gunicorn_error.log \\
    --capture-output \\
    wsgi:app'

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=audio-scheduler

[Install]
WantedBy=multi-user.target
EOF

    print_success "Service file created at: $SERVICE_DIR/audio-scheduler.service"
}

# Create required directories
create_directories() {
    print_header "Creating Required Directories"
    
    mkdir -p logs
    mkdir -p uploads
    mkdir -p instance
    mkdir -p csv-exports
    mkdir -p playlists
    
    print_success "Directories created"
}

# Initialize database
init_database() {
    print_header "Initializing Database"
    
    if [ ! -f "instance/scheduler.db" ]; then
        print_info "Creating database..."
        source venv/bin/activate
        flask db upgrade 2>/dev/null || print_warning "Database migration not needed or already up to date"
        deactivate
        print_success "Database initialized"
    else
        print_success "Database already exists"
    fi
}

# Initialize credentials
init_credentials() {
    print_header "Initializing Credentials"
    
    if [ ! -f "credentials.json" ]; then
        print_info "Creating default credentials..."
        source venv/bin/activate
        python3 << 'PYTHON_SCRIPT'
import hashlib
import json

default_password = "admin"
salt = "static_salt_for_demonstration"
hashed = hashlib.sha512((default_password + salt).encode()).hexdigest()

credentials = {
    "username": "admin",
    "password": hashed
}

with open("credentials.json", "w") as f:
    json.dump(credentials, f, indent=4)

print("Default credentials created: username=admin, password=admin")
print("⚠ IMPORTANT: Change the default password after first login!")
PYTHON_SCRIPT
        deactivate
        print_success "Credentials file created"
        print_warning "Default username: admin, password: admin"
        print_warning "Please change the password after installation!"
    else
        print_success "Credentials file already exists"
    fi
}

# Remove old service files
cleanup_old_services() {
    print_header "Cleaning Up Old Services"
    
    # Stop any running services
    if [ "$INSTALL_TYPE" = "user" ]; then
        systemctl --user stop audio-scheduler.service 2>/dev/null || true
        # Remove old system service if it exists
        if [ -f "/etc/systemd/system/audio-scheduler.service" ]; then
            print_info "Found old system-level service, attempting to remove..."
            if [ "$EUID" -eq 0 ]; then
                systemctl stop audio-scheduler.service 2>/dev/null || true
                systemctl disable audio-scheduler.service 2>/dev/null || true
                rm -f /etc/systemd/system/audio-scheduler.service
                systemctl daemon-reload
                print_success "Removed old system-level service"
            else
                print_warning "Old system-level service found at /etc/systemd/system/audio-scheduler.service"
                print_warning "Please run: sudo systemctl disable audio-scheduler.service && sudo rm /etc/systemd/system/audio-scheduler.service"
            fi
        fi
    else
        systemctl stop audio-scheduler.service 2>/dev/null || true
        # Remove old user service if it exists
        if [ -f "$HOME/.config/systemd/user/audio-scheduler.service" ]; then
            print_info "Removing old user-level service..."
            systemctl --user stop audio-scheduler.service 2>/dev/null || true
            systemctl --user disable audio-scheduler.service 2>/dev/null || true
            rm -f "$HOME/.config/systemd/user/audio-scheduler.service"
            systemctl --user daemon-reload
            print_success "Removed old user-level service"
        fi
    fi
}

# Enable and start service
enable_service() {
    print_header "Enabling and Starting Service"
    
    if [ "$INSTALL_TYPE" = "user" ]; then
        systemctl --user daemon-reload
        systemctl --user enable audio-scheduler.service
        systemctl --user start audio-scheduler.service
        
        # Enable lingering so service runs even when user is not logged in
        loginctl enable-linger "$USER" 2>/dev/null || print_warning "Could not enable user lingering (requires sudo)"
        
        print_success "Service enabled and started"
        
        # Show status
        echo ""
        systemctl --user status audio-scheduler.service --no-pager -l
    else
        systemctl daemon-reload
        systemctl enable audio-scheduler.service
        systemctl start audio-scheduler.service
        
        print_success "Service enabled and started"
        
        # Show status
        echo ""
        systemctl status audio-scheduler.service --no-pager -l
    fi
}

# Show post-installation information
show_info() {
    print_header "Installation Complete!"
    
    echo -e "${GREEN}Audio Scheduler has been successfully installed as a systemd service${NC}\n"
    
    echo -e "${BLUE}Service Management:${NC}"
    if [ "$INSTALL_TYPE" = "user" ]; then
        echo "  Start:   systemctl --user start audio-scheduler.service"
        echo "  Stop:    systemctl --user stop audio-scheduler.service"
        echo "  Restart: systemctl --user restart audio-scheduler.service"
        echo "  Status:  systemctl --user status audio-scheduler.service"
        echo "  Logs:    journalctl --user -u audio-scheduler.service -f"
    else
        echo "  Start:   sudo systemctl start audio-scheduler.service"
        echo "  Stop:    sudo systemctl stop audio-scheduler.service"
        echo "  Restart: sudo systemctl restart audio-scheduler.service"
        echo "  Status:  sudo systemctl status audio-scheduler.service"
        echo "  Logs:    sudo journalctl -u audio-scheduler.service -f"
    fi
    
    echo -e "\n${BLUE}Application Access:${NC}"
    echo "  Web Interface: http://localhost:5000"
    echo "  Default Login: admin / admin"
    echo ""
    echo -e "${YELLOW}⚠ IMPORTANT: Change the default password after first login!${NC}"
    
    echo -e "\n${BLUE}Log Files:${NC}"
    echo "  Access Log: $SCRIPT_DIR/logs/gunicorn_access.log"
    echo "  Error Log:  $SCRIPT_DIR/logs/gunicorn_error.log"
    
    echo -e "\n${BLUE}Configuration:${NC}"
    echo "  Service File: "
    if [ "$INSTALL_TYPE" = "user" ]; then
        echo "    $HOME/.config/systemd/user/audio-scheduler.service"
    else
        echo "    /etc/systemd/system/audio-scheduler.service"
    fi
    echo "  Working Directory: $SCRIPT_DIR"
    echo "  Audio System: $AUDIO_SYSTEM"
    echo ""
}

# Uninstall function
uninstall_service() {
    print_header "Uninstalling Audio Scheduler Service"
    
    read -p "Are you sure you want to uninstall the service? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Uninstall cancelled"
        exit 0
    fi
    
    if [ "$INSTALL_TYPE" = "user" ]; then
        systemctl --user stop audio-scheduler.service 2>/dev/null || true
        systemctl --user disable audio-scheduler.service 2>/dev/null || true
        rm -f "$HOME/.config/systemd/user/audio-scheduler.service"
        systemctl --user daemon-reload
        loginctl disable-linger "$USER" 2>/dev/null || true
        print_success "User-level service uninstalled"
    else
        if [ "$EUID" -ne 0 ]; then
            print_error "System-level uninstall requires root privileges"
            echo "Please run: sudo $0 --uninstall --system"
            exit 1
        fi
        systemctl stop audio-scheduler.service 2>/dev/null || true
        systemctl disable audio-scheduler.service 2>/dev/null || true
        rm -f /etc/systemd/system/audio-scheduler.service
        systemctl daemon-reload
        print_success "System-level service uninstalled"
    fi
    
    print_info "Note: Application files, database, and logs have been preserved"
    echo ""
}

# Show usage
show_usage() {
    echo "Audio Scheduler - Service Installation Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --user              Install as user-level service (recommended)"
    echo "  --system            Install as system-level service (requires sudo)"
    echo "  --uninstall         Uninstall the service"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --user                    # Install as user service"
    echo "  sudo $0 --system             # Install as system service"
    echo "  $0 --uninstall --user        # Uninstall user service"
    echo "  sudo $0 --uninstall --system # Uninstall system service"
    echo ""
}

# Main installation flow
main() {
    # Parse arguments
    INSTALL_TYPE="user"  # Default to user installation
    UNINSTALL=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --user)
                INSTALL_TYPE="user"
                shift
                ;;
            --system)
                INSTALL_TYPE="system"
                shift
                ;;
            --uninstall)
                UNINSTALL=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Handle uninstall
    if [ "$UNINSTALL" = true ]; then
        check_root
        uninstall_service
        exit 0
    fi
    
    # Installation
    print_header "Audio Scheduler - Service Installation"
    print_info "Installation type: $INSTALL_TYPE"
    
    check_root
    detect_audio_system
    get_user_id
    setup_venv
    create_directories
    init_credentials
    init_database
    cleanup_old_services
    
    if [ "$INSTALL_TYPE" = "user" ]; then
        create_user_service
    else
        create_system_service
    fi
    
    enable_service
    show_info
}

# Run main function
main "$@"
