FROM python:3.11-slim

# Install system dependencies required for OpenCV, Tesseract OCR, and general builds
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application
COPY . .

# Ensure run.sh is executable
RUN chmod +x run.sh

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Command to run the application
CMD ["./run.sh"]
