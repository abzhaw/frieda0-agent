FROM python:3.11-slim

# Install system deps (if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /workspace

# Copy only requirements first for better caching
COPY .devcontainer/requirements.txt requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Install NEAR AI CLI
RUN pip install nearai

# Copy the rest of your code
COPY . .

# Default shell
CMD ["bash"]
