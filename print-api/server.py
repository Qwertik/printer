"""Thermal Print API Server — entry point.

Creates the Flask app, initializes the job queue and printer driver,
registers API blueprints, and runs the server.
"""
import atexit
import logging
from datetime import datetime, timezone

from flask import Flask, jsonify

import config
from api import register_blueprints
from print_queue import JobQueue
from driver.printer import PrinterDriver


def create_app() -> Flask:
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    app.config['API_TOKEN'] = config.API_TOKEN
    app.config['ADMIN_TOKEN'] = config.ADMIN_TOKEN

    # Rate limiting
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[config.RATE_LIMIT],
            storage_uri="memory://",
        )
        app.extensions['limiter'] = limiter
    except ImportError:
        logging.getLogger(__name__).warning(
            "flask-limiter not installed, rate limiting disabled"
        )

    # Initialize printer driver
    printer_driver = PrinterDriver(config.PRINTER_DEVICE, config.PRINTER_BACKEND)

    # Initialize job queue
    job_queue = JobQueue(
        max_depth=config.QUEUE_MAX_DEPTH,
        job_timeout=config.JOB_TIMEOUT,
    )
    job_queue.start(printer_callback=printer_driver.print_job)

    # Store on app.extensions for access in route handlers
    app.extensions['job_queue'] = job_queue
    app.extensions['printer_driver'] = printer_driver

    # Clean shutdown
    atexit.register(job_queue.stop)
    atexit.register(printer_driver.close)

    # Register API blueprints (/api/v1/...)
    register_blueprints(app)

    # Health endpoint at root (not under /api/v1 — monitoring tools expect /health)
    @app.route('/health', methods=['GET'])
    def health():
        available = printer_driver.is_available()
        return jsonify({
            "status": "healthy" if available else "degraded",
            "printer_device": config.PRINTER_DEVICE,
            "printer_connected": available,
            "queue_depth": job_queue.depth,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 200 if available else 503

    return app


if __name__ == '__main__':
    # Configure logging
    handlers = [logging.StreamHandler()]
    if config.LOG_FILE:
        handlers.append(logging.FileHandler(config.LOG_FILE))

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        handlers=handlers,
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting print server")
    logger.info("  Device: %s (backend: %s)", config.PRINTER_DEVICE, config.PRINTER_BACKEND)
    logger.info("  Listening on: http://%s:%d", config.HOST, config.PORT)
    logger.info("  Health: http://%s:%d/health", config.HOST, config.PORT)
    logger.info("  API: http://%s:%d/api/v1/", config.HOST, config.PORT)

    app = create_app()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
