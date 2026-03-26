import logging
import time
import os
from datetime import datetime
from typing import Dict, Any

from prometheus_client import start_http_server, Counter, Gauge, Histogram, Summary
import psutil
import click

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("filemaster_cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FileMasterCLI")

# Prometheus metrics
FILES_PROCESSED = Counter(
    'filemaster_files_processed_total',
    'Total number of files processed',
    ['operation']
)

FILE_PROCESSING_DURATION = Histogram(
    'filemaster_file_processing_duration_seconds',
    'Time spent processing files',
    ['operation']
)

FILE_SIZE_BYTES = Summary(
    'filemaster_file_size_bytes',
    'Size of processed files in bytes',
    ['operation']
)

APP_UPTIME = Gauge('filemaster_app_uptime_seconds', 'Uptime of the application in seconds')
SYSTEM_DISK_USAGE = Gauge('filemaster_system_disk_usage_percent', 'System disk usage in percent')
SYSTEM_MEMORY_USAGE = Gauge('filemaster_system_memory_usage_percent', 'System memory usage in percent')
ACTIVE_OPERATIONS = Gauge('filemaster_active_operations', 'Number of currently active file operations', ['operation'])

# Health check metrics
HEALTH_STATUS = Gauge('filemaster_health_status', 'Health status of the service (1=healthy, 0=unhealthy)')
LAST_SUCCESSFUL_RUN = Gauge('filemaster_last_successful_run_timestamp', 'Timestamp of last successful operation')

class FileMasterCLI:
    def __init__(self):
        self.start_time = time.time()
        self.last_successful_run = 0
        self.register_metrics()

    def register_metrics(self):
        """Register metrics that need periodic updating"""
        APP_UPTIME.set_function(lambda: time.time() - self.start_time)
        SYSTEM_DISK_USAGE.set_function(lambda: psutil.disk_usage('/').percent)
        SYSTEM_MEMORY_USAGE.set_function(lambda: psutil.virtual_memory().percent)
        HEALTH_STATUS.set_function(self.health_check)

    def health_check(self) -> float:
        """Perform health check and return 1.0 if healthy, 0.0 otherwise"""
        try:
            # Check disk space
            disk_usage = psutil.disk_usage('/')
            if disk_usage.percent > 95:
                logger.error("Health check failed: disk usage above 95%")
                return 0.0

            # Check if we can write to current directory
            test_file = '.health_check.tmp'
            with open(test_file, 'w') as f:
                f.write('health check')
            os.remove(test_file)

            # Check process memory
            process = psutil.Process()
            if process.memory_percent() > 80:
                logger.error("Health check failed: process memory usage above 80%")
                return 0.0

            return 1.0
        except Exception as e:
            logger.error(f"Health check failed with exception: {e}")
            return 0.0

    def update_last_successful_run(self):
        """Update the last successful run timestamp"""
        self.last_successful_run = time.time()
        LAST_SUCCESSFUL_RUN.set(self.last_successful_run)

    @FILE_PROCESSING_DURATION.labels(operation="copy").time()
    def copy_file(self, src: str, dst: str) -> bool:
        """Copy a file with monitoring"""
        if not os.path.exists(src):
            logger.error(f"Source file does not exist: {src}")
            return False

        ACTIVE_OPERATIONS.labels(operation="copy").inc()
        start_time = time.time()
        
        try:
            file_size = os.path.getsize(src)
            FILE_SIZE_BYTES.labels(operation="copy").observe(file_size)
            
            # Simulate file copy
            with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                fdst.write(fsrc.read())
            
            duration = time.time() - start_time
            logger.info(f"File copied successfully", extra={
                'operation': 'copy',
                'src': src,
                'dst': dst,
                'size_bytes': file_size,
                'duration_seconds': round(duration, 3),
                'status': 'success'
            })
            
            FILES_PROCESSED.labels(operation="copy").inc()
            self.update_last_successful_run()
            return True
            
        except Exception as e:
            logger.error(f"File copy failed", extra={
                'operation': 'copy',
                'src': src,
                'dst': dst,
                'error': str(e),
                'status': 'failed'
            })
            return False
        finally:
            ACTIVE_OPERATIONS.labels(operation="copy").dec()

    @FILE_PROCESSING_DURATION.labels(operation="move").time()
    def move_file(self, src: str, dst: str) -> bool:
        """Move a file with monitoring"""
        if not os.path.exists(src):
            logger.error(f"Source file does not exist: {src}")
            return False

        ACTIVE_OPERATIONS.labels(operation="move").inc()
        start_time = time.time()
        
        try:
            file_size = os.path.getsize(src)
            FILE_SIZE_BYTES.labels(operation="move").observe(file_size)
            
            # Simulate file move
            os.rename(src, dst)
            
            duration = time.time() - start_time
            logger.info(f"File moved successfully", extra={
                'operation': 'move',
                'src': src,
                'dst': dst,
                'size_bytes': file_size,
                'duration_seconds': round(duration, 3),
                'status': 'success'
            })
            
            FILES_PROCESSED.labels(operation="move").inc()
            self.update_last_successful_run()
            return True
            
        except Exception as e:
            logger.error(f"File move failed", extra={
                'operation': 'move',
                'src': src,
                'dst': dst,
                'error': str(e),
                'status': 'failed'
            })
            return False
        finally:
            ACTIVE_OPERATIONS.labels(operation="move").dec()

    @FILE_PROCESSING_DURATION.labels(operation="delete").time()
    def delete_file(self, path: str) -> bool:
        """Delete a file with monitoring"""
        if not os.path.exists(path):
            logger.warning(f"File to delete does not exist: {path}")
            return True  # Idempotent operation

        ACTIVE_OPERATIONS.labels(operation="delete").inc()
        start_time = time.time()
        
        try:
            file_size = os.path.getsize(path)
            
            # Simulate file deletion
            os.remove(path)
            
            duration = time.time() - start_time
            logger.info(f"File deleted successfully", extra={
                'operation': 'delete',
                'path': path,
                'size_bytes': file_size,
                'duration_seconds': round(duration, 3),
                'status': 'success'
            })
            
            FILES_PROCESSED.labels(operation="delete").inc()
            self.update_last_successful_run()
            return True
            
        except Exception as e:
            logger.error(f"File deletion failed", extra={
                'operation': 'delete',
                'path': path,
                'error': str(e),
                'status': 'failed'
            })
            return False
        finally:
            ACTIVE_OPERATIONS.labels(operation="delete").dec()

    def list_directory(self, path: str) -> list:
        """List directory contents with monitoring"""
        if not os.path.exists(path):
            logger.error(f"Directory does not exist: {path}")
            return []

        try:
            files = os.listdir(path)
            logger.info(f"Directory listed", extra={
                'operation': 'list',
                'path': path,
                'file_count': len(files),
                'status': 'success'
            })
            return files
        except Exception as e:
            logger.error(f"Directory listing failed", extra={
                'operation': 'list',
                'path': path,
                'error': str(e),
                'status': 'failed'
            })
            return []

# Prometheus alerting rules (as Python dictionary for configuration)
ALERTING_RULES = {
    "groups": [
        {
            "name": "FileMasterAlerts",
            "rules": [
                {
                    "alert": "HighFileProcessingLatency",
                    "expr": "rate(filemaster_file_processing_duration_seconds_sum[5m]) / rate(filemaster_file_processing_duration_seconds_count[5m]) > 10",
                    "for": "10m",
                    "labels": {
                        "severity": "warning"
                    },
                    "annotations": {
                        "summary": "High file processing latency",
                        "description": "File processing is taking more than 10 seconds on average over the last 5 minutes."
                    }
                },
                {
                    "alert": "LowHealthStatus",
                    "expr": "filemaster_health_status == 0",
                    "for": "2m",
                    "labels": {
                        "severity": "critical"
                    },
                    "annotations": {
                        "summary": "FileMaster CLI is unhealthy",
                        "description": "The health check for FileMaster CLI has been failing for more than 2 minutes."
                    }
                },
                {
                    "alert": "HighDiskUsage",
                    "expr": "filemaster_system_disk_usage_percent > 90",
                    "for": "5m",
                    "labels": {
                        "severity": "warning"
                    },
                    "annotations": {
                        "summary": "High disk usage",
                        "description": "System disk usage is above 90% for more than 5 minutes."
                    }
                },
                {
                    "alert": "NoRecentActivity",
                    "expr": "time() - filemaster_last_successful_run_timestamp > 3600",
                    "for": "1m",
                    "labels": {
                        "severity": "warning"
                    },
                    "annotations": {
                        "summary": "No recent successful operations",
                        "description": "No successful file operations in the last hour."
                    }
                },
                {
                    "alert": "HighMemoryUsage",
                    "expr": "filemaster_system_memory_usage_percent > 85",
                    "for": "10m",
                    "labels": {
                        "severity": "warning"
                    },
                    "annotations": {
                        "summary": "High memory usage",
                        "description": "System memory usage is above 85% for more than 10 minutes."
                    }
                }
            ]
        }
    ]
}

@click.group()
def cli():
    """FileMaster CLI - File management with monitoring"""
    pass

@cli.command()
@click.argument('src')
@click.argument('dst')
def copy(src, dst):
    """Copy a file from source to destination"""
    fm = FileMasterCLI()
    success = fm.copy_file(src, dst)
    if not success:
        exit(1)

@cli.command()
@click.argument('src')
@click.argument('dst')
def move(src, dst):
    """Move a file from source to destination"""
    fm = FileMasterCLI()
    success = fm.move_file(src, dst)
    if not success:
        exit(1)

@cli.command()
@click.argument('path')
def delete(path):
    """Delete a file"""
    fm = FileMasterCLI()
    success = fm.delete_file(path)
    if not success:
        exit(1)

@cli.command()
@click.argument('path', default='.')
def list(path):
    """List files in a directory"""
    fm = FileMasterCLI()
    files = fm.list_directory(path)
    for file in files:
        print(file)

@cli.command()
@click.option('--port', default=8000, help='Port for metrics server')
def metrics(port):
    """Start the metrics server"""
    logger.info(f"Starting metrics server on port {port}")
    start_http_server(port)
    
    # Keep the server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Metrics server stopped")

if __name__ == '__main__':
    cli()