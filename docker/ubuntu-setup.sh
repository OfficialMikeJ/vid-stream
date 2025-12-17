#!/bin/bash

# StreamHost - Ubuntu 20.04+ Docker Setup Script
# Version: 2025.12.17

set -e

echo "=============================================="
echo "  StreamHost Docker Setup for Ubuntu 20.04+"
echo "  Version: 2025.12.17"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo ./ubuntu-setup.sh)${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/6] Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

echo -e "${YELLOW}[2/6] Installing prerequisites...${NC}"
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common

echo -e "${YELLOW}[3/6] Installing Docker...${NC}"
# Remove old versions if any
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Add Docker's official GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo -e "${YELLOW}[4/6] Starting Docker service...${NC}"
systemctl start docker
systemctl enable docker

echo -e "${YELLOW}[5/6] Adding current user to docker group...${NC}"
if [ -n "$SUDO_USER" ]; then
    usermod -aG docker $SUDO_USER
    echo -e "${GREEN}User $SUDO_USER added to docker group${NC}"
fi

echo -e "${YELLOW}[6/6] Verifying installation...${NC}"
docker --version
docker compose version

echo ""
echo -e "${GREEN}=============================================="
echo "  Docker Installation Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Log out and log back in (for docker group changes)"
echo "  2. Navigate to your StreamHost directory"
echo "  3. Copy .env.docker to .env and configure"
echo "  4. Run: docker compose up -d"
echo ""
echo "Default credentials:"
echo "  Username: StreamHost"
echo "  Password: password1234!@#"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8001"
echo "==============================================${NC}"
