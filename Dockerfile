# Stage 1: Base Image
FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install minimal runtime libs (with retries), then Python deps
RUN apt-get update -o Acquire::Retries=3 \
    && apt-get install -y --no-install-recommends libgomp1 libopenblas0 libstdc++6 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "app.api.api_server:app", "--host", "0.0.0.0", "--port", "8080"]