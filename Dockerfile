FROM python:3.11-slim

# Run as non-root — never run production containers as root
RUN useradd -m -u 1001 appuser

WORKDIR /app

# Install deps before copying app code — maximises Docker layer cache hits
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Streamlit config — disable telemetry, fix port
RUN mkdir -p /home/appuser/.streamlit && \
    echo '[server]\nport = 8502\naddress = "0.0.0.0"\nheadless = true\n\n[browser]\ngatherUsageStats = false\n\n[client]\nshowErrorDetails = false' \
    > /home/appuser/.streamlit/config.toml && \
    chown -R appuser:appuser /home/appuser/.streamlit

USER appuser

EXPOSE 8502

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8502/_stcore/health', timeout=4).raise_for_status()"

CMD ["streamlit", "run", "app.py"]