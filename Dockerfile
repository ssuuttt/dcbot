# Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .



RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg curl

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script to the working directory
# COPY discord_bot.py .

# Run the script
CMD ["python", "discord_bot.py"]
