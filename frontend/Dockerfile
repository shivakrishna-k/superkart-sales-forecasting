# Use a minimal base image with Python 3.11 installed
FROM python:3.11-slim

# Set the working directory inside the container to /app
WORKDIR /app

# Install the Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit application into the container
COPY . .

# Streamlit listens on port 8501
EXPOSE 8501

# Run the Streamlit app on port 8501 and make it accessible externally.
# XSRF protection is disabled so file uploads work through the Codespaces port-forwarding proxy.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]
