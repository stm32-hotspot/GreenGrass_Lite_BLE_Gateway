#!/bin/bash

# Check if tomllib can be imported
python3 -c "import tomllib" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "tomllib not found, installing dependencies..."

  # Update apt package list
  apt-get update

  # Install full version of python3
  apt-get install -y --reinstall python3

  # Try importing tomllib again to check if the issue is resolved
  python3 -c "import tomllib" 2>/dev/null
  if [ $? -ne 0 ]; then
    echo "Failed to install tomllib"
  else
    echo "Successfully installed tomllib"
  fi
else
  echo "tomllib is already installed."
fi

# Install pip3 if it's not already installed
apt-get install -y python3-pip

# Install necessary Python packages
pip3 install bleak>=0.22.3 paho-mqtt>=2.1.0
echo "Packages bleak and paho-mqtt have been installed."
