#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then 
    print_color $RED "Please run as root (use sudo)"
    exit 1
fi

# Update package list and upgrade existing packages
print_color $YELLOW "Updating and upgrading packages..."
apt update && apt upgrade -y

# Install system dependencies
print_color $YELLOW "Installing system dependencies..."
apt install -y python3 python3-pip python3-venv git redis-server

# Set up project directory
PROJECT_NAME="ai-telegram-ftp-server"
PROJECT_DIR="/opt/$PROJECT_NAME"

if [ -d "$PROJECT_DIR" ]; then
    print_color $YELLOW "Project directory already exists. Updating..."
    cd "$PROJECT_DIR"
    git pull
else
    print_color $YELLOW "Creating project directory..."
    git clone https://github.com/yourusername/$PROJECT_NAME.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# Create and activate virtual environment
print_color $YELLOW "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_color $YELLOW "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install YOLO dependencies
print_color $YELLOW "Installing YOLO dependencies..."
pip install ultralytics

# Download YOLO model
print_color $YELLOW "Downloading YOLO model..."
python3 -c "from ultralytics import YOLO; YOLO('yolov5l.pt')"

# Create necessary directories
print_color $YELLOW "Creating necessary directories..."
mkdir -p {ftp_root,positive_photos,logs}

# Set up configuration
if [ ! -f config.py ]; then
    print_color $YELLOW "Setting up configuration file..."
    cat > config.py << EOF
# FTP Server Configuration
FTP_HOST = '0.0.0.0'
FTP_PORT = 21
MAIN_FTP_DIRECTORY = '${PROJECT_DIR}/ftp_root'
POSITIVE_PHOTOS_DIRECTORY = '${PROJECT_DIR}/positive_photos'
MAX_IMAGE_QUEUE = 100

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# Redis Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = ''
REDIS_ARMED_KEY_PREFIX = 'armed:'

# YOLO Model Configuration
YOLO_MODEL = 'yolov5s.pt'

# User Configuration
USERS = {
    'user1': {
        'FTP_USER': 'ftpuser1',
        'FTP_PASS': 'ftppass1',
        'TELEGRAM_CHAT_ID': 'YOUR_TELEGRAM_CHAT_ID',
        'SIGNL4_SECRET': 'YOUR_SIGNL4_SECRET',
        'ARMED': True,
        'ENABLE_PERSON_DETECTION': True,
        'ENABLE_VEHICLE_DETECTION': True,
        'ENABLE_ANIMAL_DETECTION': True,
        'PERSON_CONFIDENCE_THRESHOLD': 0.5,
        'VEHICLE_CONFIDENCE_THRESHOLD': 0.5,
        'ANIMAL_CONFIDENCE_THRESHOLD': 0.5,
        'WORKING_START_TIME': '08:00',
        'WORKING_END_TIME': '18:00',
        'WATERMARK_TEXT': '{username} - {timestamp}'
    }
}
EOF
    print_color $GREEN "Configuration file created. Please edit config.py with your specific settings."
else
    print_color $YELLOW "Configuration file already exists. Skipping..."
fi

# Create startup script
print_color $YELLOW "Creating startup script..."
cat > start.sh << EOF
#!/bin/bash
source ${PROJECT_DIR}/venv/bin/activate
python ${PROJECT_DIR}/app.py
EOF
chmod +x start.sh

# Create systemd service file
print_color $YELLOW "Creating systemd service file..."
cat > /etc/systemd/system/ai-telegram-ftp-server.service << EOF
[Unit]
Description=AI Telegram FTP Server
After=network.target

[Service]
ExecStart=${PROJECT_DIR}/start.sh
WorkingDirectory=${PROJECT_DIR}
User=root
Group=root
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
systemctl daemon-reload
systemctl enable ai-telegram-ftp-server.service
systemctl start ai-telegram-ftp-server.service

print_color $GREEN "Installation completed successfully!"
print_color $GREEN "The AI Telegram FTP Server service has been started and enabled to run on boot."
print_color $YELLOW "Make sure to edit ${PROJECT_DIR}/config.py with your specific settings."
print_color $YELLOW "You can manage the service with these commands:"
print_color $YELLOW "  - Check status: sudo systemctl status ai-telegram-ftp-server"
print_color $YELLOW "  - Restart: sudo systemctl restart ai-telegram-ftp-server"
print_color $YELLOW "  - Stop: sudo systemctl stop ai-telegram-ftp-server"
print_color $YELLOW "  - View logs: sudo journalctl -u ai-telegram-ftp-server"