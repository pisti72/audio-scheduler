#!/bin/bash
set -e

# Audio Scheduler - Automated Installation Script
# This script will set up a virtual environment and install all dependencies

echo "🎵 Audio Scheduler - Automated Installation 🎵"
echo "================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root (for security reasons)"
   print_status "Please run as a regular user. The script will ask for sudo when needed."
   exit 1
fi

# Function to detect the operating system
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        print_error "Cannot detect operating system"
        exit 1
    fi
}

# Function to install system dependencies
install_system_deps() {
    print_status "Installing system dependencies for $OS..."
    
    case $OS in
        "fedora"|"rhel"|"centos"|"rocky"|"almalinux")
            print_status "Installing packages for Red Hat-based system..."
            sudo dnf update -y || print_warning "Failed to update package list"
            # Install packages one by one to handle already installed packages gracefully
            packages=(
                "python3" "python3-pip" "python3-devel"
                "gcc" "gcc-c++" "make" "cmake"
                "SDL2-devel" "SDL2_mixer-devel" "SDL2_image-devel" "SDL2_ttf-devel"
                "portmidi-devel" "alsa-lib-devel"
                "git" "curl" "wget"
            )
            for package in "${packages[@]}"; do
                sudo dnf install -y "$package" || print_warning "Package $package may already be installed or unavailable"
            done
            # Note: python3-venv is built into python3 on modern Fedora
            ;;
        "ubuntu"|"debian"|"pop"|"elementary"|"linuxmint")
            print_status "Installing packages for Debian-based system..."
            sudo apt-get update || print_warning "Failed to update package list"
            sudo apt-get install -y python3 python3-pip python3-venv python3-dev \
                                   build-essential cmake \
                                   libsdl2-dev libsdl2-mixer-dev libsdl2-image-dev libsdl2-ttf-dev \
                                   libportmidi-dev libasound2-dev \
                                   git curl wget || print_warning "Some packages may already be installed"
            ;;
        "opensuse"|"opensuse-leap"|"opensuse-tumbleweed")
            print_status "Installing packages for openSUSE..."
            sudo zypper refresh || print_warning "Failed to refresh repositories"
            sudo zypper install -y python3 python3-pip python3-devel \
                                  gcc gcc-c++ make cmake \
                                  libSDL2-devel libSDL2_mixer-devel libSDL2_image-devel libSDL2_ttf-devel \
                                  portmidi-devel alsa-devel \
                                  git curl wget || print_warning "Some packages may already be installed"
            ;;
        "arch"|"manjaro")
            print_status "Installing packages for Arch-based system..."
            sudo pacman -Syu --noconfirm || print_warning "Failed to update system"
            sudo pacman -S --noconfirm python python-pip \
                                      base-devel cmake \
                                      sdl2 sdl2_mixer sdl2_image sdl2_ttf \
                                      portmidi alsa-lib \
                                      git curl wget || print_warning "Some packages may already be installed"
            ;;
        *)
            print_warning "Unsupported operating system: $OS"
            print_status "Please manually install the following packages:"
            print_status "- Python 3.8+ with pip and venv"
            print_status "- Development tools (gcc, make, cmake)"
            print_status "- SDL2 development libraries"
            print_status "- PortMidi development libraries"
            print_status "- ALSA development libraries"
            read -p "Press Enter to continue with Python setup (assuming dependencies are installed)..."
            ;;
    esac
}

# Check Python version
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python not found. Please install Python 3.8 or newer."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ $MAJOR -eq 3 ] && [ $MINOR -ge 8 ]; then
        print_success "Python $PYTHON_VERSION found ✓"
    else
        print_error "Python 3.8 or newer is required. Found: $PYTHON_VERSION"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            print_status "Removed existing virtual environment"
        else
            print_status "Using existing virtual environment"
            return
        fi
    fi
    
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created ✓"
}

# Activate virtual environment and install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    pip install -r requirements.txt
    
    print_success "Python dependencies installed ✓"
}

# Initialize the application
init_app() {
    print_status "Initializing application..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Create necessary directories
    mkdir -p uploads
    mkdir -p instance
    
    # Initialize database if it doesn't exist
    if [ ! -f "schedules.db" ]; then
        print_status "Initializing database..."
        python app.py --init-only &
        sleep 3
        pkill -f "python app.py" || true
        print_success "Database initialized ✓"
    fi
    
    print_success "Application initialized ✓"
}

# Create run script
create_run_script() {
    print_status "Setting up run script..."
    
    if [ -f "run.sh" ]; then
        print_success "Run script already exists ✓"
        chmod +x run.sh
        return
    fi
    
    print_status "Creating run script..."
    cat > run.sh << 'EOF'
#!/bin/bash
# Audio Scheduler - Run Script

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./install.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if all dependencies are installed
if ! python -c "import flask, pygame, sqlalchemy" 2>/dev/null; then
    echo "❌ Dependencies not properly installed!"
    echo "Please run ./install.sh again"
    exit 1
fi

echo "🎵 Starting Audio Scheduler..."
echo "📡 Server will be available at: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Run the application
python app.py
EOF

    chmod +x run.sh
    print_success "Run script created ✓"
}

# Main installation process
main() {
    echo ""
    print_status "Starting installation process..."
    echo ""
    
    # Step 1: Detect OS
    detect_os
    print_success "Detected OS: $OS"
    
    # Step 2: Install system dependencies
    echo ""
    print_status "Step 1/5: Installing system dependencies..."
    install_system_deps
    print_success "System dependencies installed ✓"
    
    # Step 3: Check Python
    echo ""
    print_status "Step 2/5: Checking Python installation..."
    check_python
    
    # Step 4: Create virtual environment
    echo ""
    print_status "Step 3/5: Setting up virtual environment..."
    create_venv
    
    # Step 5: Install Python dependencies
    echo ""
    print_status "Step 4/5: Installing Python dependencies..."
    install_python_deps
    
    # Step 6: Initialize application
    echo ""
    print_status "Step 5/5: Initializing application..."
    init_app
    
    # Step 7: Create run script
    create_run_script
    
    # Installation complete
    echo ""
    echo "🎉 Installation completed successfully! 🎉"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Run the application:  ./run.sh"
    echo "  2. Open your browser:    http://localhost:5000"
    echo "  3. Default credentials:  admin / admin"
    echo ""
    echo "📚 For more information, check the README.md file"
    echo ""
    
    # Ask if user wants to start the application now
    read -p "Do you want to start the application now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Starting Audio Scheduler..."
        ./run.sh
    fi
}

# Run main function
main "$@"