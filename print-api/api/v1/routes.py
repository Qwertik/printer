from datetime import datetime, timezone
from flask import request, jsonify, current_app

from . import v1_bp
from .auth import require_auth, require_admin
from .validation import validate_print_request, validate_raw_request
from print_queue.job import PrintJob


@v1_bp.route('/print', methods=['POST'])
@require_auth
def print_receipt():
    """Submit a structured print job. Returns 202 with job_id."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    cleaned, errors = validate_print_request(data)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    job_queue = current_app.extensions['job_queue']
    job = PrintJob(payload=cleaned, client_ip=request.remote_addr)

    if not job_queue.submit(job):
        return jsonify({"error": "Queue full, try again later"}), 429

    return jsonify({
        "status": "queued",
        "job_id": job.id,
        "queue_depth": job_queue.depth,
    }), 202


@v1_bp.route('/print/raw', methods=['POST'])
@require_admin
def print_raw():
    """Submit raw base64-encoded ESC/POS bytes (admin only). Returns 202 with job_id."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    raw_bytes, errors = validate_raw_request(data)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    job_queue = current_app.extensions['job_queue']
    job = PrintJob(
        payload={"raw_data": raw_bytes},
        client_ip=request.remote_addr,
        is_raw=True,
    )

    if not job_queue.submit(job):
        return jsonify({"error": "Queue full, try again later"}), 429

    return jsonify({
        "status": "queued",
        "job_id": job.id,
        "queue_depth": job_queue.depth,
    }), 202


@v1_bp.route('/status', methods=['GET'])
@require_auth
def status():
    """Printer and job status. Optional ?job_id= for specific job lookup."""
    job_queue = current_app.extensions['job_queue']
    printer_driver = current_app.extensions['printer_driver']

    job_id = request.args.get('job_id')
    if job_id:
        job = job_queue.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        return jsonify({
            "job_id": job.id,
            "state": job.state.value,
            "error": job.error,
        }), 200

    return jsonify({
        "printer": "connected" if printer_driver.is_available() else "disconnected",
        "queue_depth": job_queue.depth,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200
