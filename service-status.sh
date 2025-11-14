#!/bin/bash
#
# Audio Scheduler - Quick Status Check
# Shows service status and recent logs
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Audio Scheduler - Service Status${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if user service exists
if [ -f "$HOME/.config/systemd/user/audio-scheduler.service" ]; then
    echo -e "${GREEN}User Service Found${NC}"
    echo -e "\n${BLUE}Service Status:${NC}"
    systemctl --user status audio-scheduler.service --no-pager | head -15
    
    echo -e "\n${BLUE}Recent Logs (last 10 lines):${NC}"
    journalctl --user -u audio-scheduler.service -n 10 --no-pager
    
    echo -e "\n${BLUE}Quick Commands:${NC}"
    echo "  Start:   systemctl --user start audio-scheduler.service"
    echo "  Stop:    systemctl --user stop audio-scheduler.service"
    echo "  Restart: systemctl --user restart audio-scheduler.service"
    echo "  Logs:    journalctl --user -u audio-scheduler.service -f"
    
elif [ -f "/etc/systemd/system/audio-scheduler.service" ]; then
    echo -e "${YELLOW}System Service Found (requires sudo)${NC}"
    echo -e "\n${BLUE}Service Status:${NC}"
    sudo systemctl status audio-scheduler.service --no-pager | head -15
    
    echo -e "\n${BLUE}Recent Logs (last 10 lines):${NC}"
    sudo journalctl -u audio-scheduler.service -n 10 --no-pager
    
    echo -e "\n${BLUE}Quick Commands:${NC}"
    echo "  Start:   sudo systemctl start audio-scheduler.service"
    echo "  Stop:    sudo systemctl stop audio-scheduler.service"
    echo "  Restart: sudo systemctl restart audio-scheduler.service"
    echo "  Logs:    sudo journalctl -u audio-scheduler.service -f"
    
else
    echo -e "${RED}No service installation found${NC}"
    echo ""
    echo "Install with:"
    echo "  ./install-service.sh --user    (recommended)"
    echo "  sudo ./install-service.sh --system"
    exit 1
fi

echo -e "\n${BLUE}Application Logs:${NC}"
if [ -f "logs/gunicorn_error.log" ]; then
    echo "Last 5 log entries:"
    tail -5 logs/gunicorn_error.log
else
    echo "No application logs found"
fi

echo -e "\n${BLUE}Web Interface:${NC}"
echo "  http://localhost:5000"

echo ""
