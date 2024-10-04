#!/bin/bash

# Function to handle critical errors
handle_error() {
    echo "Error: $1"
    exit 1
}

# Check for system updates and upgrade if necessary
echo "Checking for system updates..."
sudo apt update || handle_error "Failed to update package lists."

UPDATES=$(apt list --upgradable 2>/dev/null | wc -l)
if [ "$UPDATES" -gt 1 ]; then
    echo "System updates are available. Upgrading..."
    sudo apt full-upgrade -y || handle_error "Failed to upgrade packages."
    sudo apt autoremove -y || echo "Warning: Failed to autoremove packages."
    sudo apt clean || echo "Warning: Failed to clean packages."
else
    echo "System is up to date."
fi

# Install ffmpeg if not already installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing ffmpeg..."
    sudo apt install -y ffmpeg || handle_error "Failed to install ffmpeg."
else
    echo "ffmpeg is already installed."
fi

# Install nvidia-cuda-toolkit and NVIDIA drivers
if ! command -v nvcc &> /dev/null; then
    echo "Installing nvidia-cuda-toolkit and nvidia-driver-525"
    
    # Install NVIDIA CUDA toolkit
    sudo apt install -y nvidia-cuda-toolkit || handle_error "Failed to install nvidia-cuda-toolkit."
    
    # Install NVIDIA drivers
    sudo apt install -y nvidia-driver-525 || handle_error "Failed to install nvidia-driver-525."
else
    echo "nvidia-cuda-toolkit is already installed."
fi

# Install necessary packages
echo "Installing necessary packages..."
sudo apt install -y git python3-pip python3-venv || handle_error "Failed to install required packages."

# Add alias for 'py' to call 'python3' if it doesn't exist
echo "Adding alias for 'py'..."
if ! grep -q "alias py='python3'" ~/.bashrc; then
    echo "alias py='python3'" >> ~/.bashrc || handle_error "Failed to add alias to ~/.bashrc."
    echo "Alias 'py' added to ~/.bashrc"
    # Make the alias available in the current session
    alias py='python3'
else
    echo "Alias 'py' already exists."
fi

# Create the /ai directory with appropriate permissions
echo "Setting up /ai directory..."
if [ ! -d "/ai" ]; then
    sudo mkdir -p /ai || handle_error "Failed to create /ai directory."
    sudo chown "$USER:$USER" /ai || handle_error "Failed to change ownership of /ai."
    sudo chmod 755 /ai || handle_error "Failed to set permissions for /ai."
    echo "/ai directory created with proper permissions."
else
    echo "/ai directory already exists."
    # Check ownership and permissions
    OWNER=$(stat -c '%U' /ai)
    if [ "$OWNER" != "$USER" ]; then
        sudo chown -R "$USER:$USER" /ai || handle_error "Failed to change ownership of /ai and its contents."
    fi
    PERMS=$(stat -c '%A' /ai)
    if [ "$PERMS" != "drwxr-xr-x" ]; then
        sudo chmod -R u+rwX /ai || handle_error "Failed to set permissions for /ai and its contents."
    fi
fi

# Ensure /ai is not a git repository
if [ -d "/ai/.git" ]; then
    echo "/ai is a git repository. Removing .git directory to prevent conflicts."
    rm -rf /ai/.git || handle_error "Failed to remove existing /ai/.git directory."
fi

# Clone the GitHub repository if it hasn't been cloned already
REPO_DIR="/ai/whisper"
REPO_URL="https://github.com/Mushkrot/whisper.git"

echo "Checking if the repository is already cloned..."
if [ ! -d "$REPO_DIR/.git" ]; then
    echo "Cloning the repository..."
    git clone "$REPO_URL" "$REPO_DIR" --depth 1 || handle_error "Failed to clone the repository."
    echo "Repository cloned into $REPO_DIR."
else
    echo "Repository already cloned."
    cd "$REPO_DIR" || handle_error "Failed to navigate to repository directory."
    # Check for local changes
    if [ -n "$(git status --porcelain)" ]; then
        echo "Local changes detected. Stashing before pulling updates."
        git stash || handle_error "Failed to stash local changes."
        STASHED=true
    fi
    # Pull latest changes
    git pull || handle_error "Failed to pull latest changes."
    if [ "$STASHED" = true ]; then
        echo "Applying stashed changes."
        git stash pop || echo "No stashed changes to apply."
    fi
    cd - >/dev/null || handle_error "Failed to return to previous directory."
fi

# Ensure the user owns all files in /ai/whisper
sudo chown -R "$USER:$USER" "$REPO_DIR" || handle_error "Failed to change ownership of $REPO_DIR and its contents."
sudo chmod -R u+rwX "$REPO_DIR" || handle_error "Failed to set permissions for $REPO_DIR and its contents."

# Create a virtual environment if it doesn't exist or is invalid
VENV_DIR="$REPO_DIR/venv"
echo "Checking for existing virtual environment..."
if [ -d "$VENV_DIR" ]; then
    if [ -f "$VENV_DIR/bin/activate" ]; then
        echo "Virtual environment already exists."
    else
        echo "Existing virtual environment directory found but not valid. Removing and recreating..."
        rm -rf "$VENV_DIR" || handle_error "Failed to remove invalid virtual environment directory."
        echo "Creating virtual environment in $VENV_DIR..."
        python3 -m venv "$VENV_DIR" || handle_error "Failed to create virtual environment."
        echo "Virtual environment created."
    fi
else
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR" || handle_error "Failed to create virtual environment."
    echo "Virtual environment created."
fi

# Activate the virtual environment
echo "Activating the virtual environment..."
source "$VENV_DIR/bin/activate" || handle_error "Failed to activate virtual environment."

# Upgrade pip to the latest version
echo "Upgrading pip..."
pip install --upgrade pip || handle_error "Failed to upgrade pip."

# Install PyTorch with CUDA 11.5 support
echo "Installing PyTorch with CUDA 11.5 support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu115 || handle_error "Failed to install PyTorch with CUDA 11.5."

# Install dependencies from requirements.txt if it exists
REQUIREMENTS_FILE="$REPO_DIR/requirements.txt"
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE" || handle_error "Failed to install dependencies from requirements.txt."
    echo "Dependencies installed."
else
    echo "requirements.txt not found at $REQUIREMENTS_FILE. Skipping dependency installation."
fi

echo "Virtual environment is set up and dependencies are installed."

# Deactivate the virtual environment
deactivate || echo "Warning: Failed to deactivate virtual environment."

# Reminder to the user
echo "To activate the virtual environment later, run:"
echo "source $VENV_DIR/bin/activate"

echo "Script completed successfully."
