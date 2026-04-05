FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces require running as a non-root user (uid 1000)
RUN useradd -m -u 1000 user
WORKDIR /app
RUN chown user:user /app
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Copy application code first so we can install as a package
COPY --chown=user:user . .

# Install the project and dependencies
RUN pip install --user --no-cache-dir .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=7860
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Run the application
CMD ["server"]
