#!/bin/bash

# Function to handle critical errors
handle_error() {
    echo "Error: $1"
    exit 1
}

# Update and upgrade the system
echo "Updating and upgrading the system..."
sudo apt update || handle_error "Failed to update package lists."
sudo apt full-upgrade -y || handle_error "Failed to upgrade packages."
sudo apt autoremove -y || echo "Warning: Failed to autoremove packages."
sudo apt clean || echo "Warning: Failed to clean packages."

sudo apt install -y ffmpeg || handle_error "Failed to install required packages."

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
    sudo chown $USER:$USER /ai || handle_error "Failed to change ownership of /ai."
    sudo chmod 755 /ai || handle_error "Failed to set permissions for /ai."
    echo "/ai directory created with proper permissions."
else
    echo "/ai directory already exists."
    sudo chown -R $USER:$USER /ai || handle_error "Failed to change ownership of /ai and its contents."
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
    git clone $REPO_URL $REPO_DIR --depth 1 || handle_error "Failed to clone the repository."
    echo "Repository cloned into $REPO_DIR."
else
    echo "Repository already cloned, pulling latest changes..."
    cd $REPO_DIR || handle_error "Failed to navigate to repository directory."
    # Forcefully reset local changes and match remote
    git fetch origin || handle_error "Failed to fetch changes from origin."
    # Determine the default branch (master or main)
    DEFAULT_BRANCH=$(git remote show origin | grep "HEAD branch" | awk '{print $NF}')
    git reset --hard origin/$DEFAULT_BRANCH || handle_error "Failed to reset local branch to origin/$DEFAULT_BRANCH."
    cd - >/dev/null || handle_error "Failed to return to previous directory."
fi

# Create a virtual environment if it doesn't exist or is invalid
VENV_DIR="/ai/whisper/venv"
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

# (Optional) Add commands to run your application here
# For example:
# python3 your_script.py

# Deactivate the virtual environment
deactivate || echo "Warning: Failed to deactivate virtual environment."

echo "Script completed successfully."
