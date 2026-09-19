# Use official lightweight Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY backend /app/backend
COPY frontend /app/frontend

# Environment variable for port
ENV PORT=5000

# Expose port
EXPOSE 5000

# Run the server
CMD ["python", "backend/server.py", "5000"]
