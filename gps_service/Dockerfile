FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install gps_service deps only (no backend deps).
COPY gps_service/requirements.txt ./gps_service/requirements.txt
RUN pip install --no-cache-dir -r ./gps_service/requirements.txt

# Copy the package as a subdirectory so `python -m gps_service.main` works
# and all `from gps_service.x import y` imports resolve.
COPY gps_service/ ./gps_service/
COPY pyproject.toml ./

EXPOSE 8001

CMD ["python", "-m", "gps_service.main"]
