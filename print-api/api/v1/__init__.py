from flask import Blueprint

v1_bp = Blueprint('v1', __name__, url_prefix='/api/v1')

from . import routes  # noqa: E402, F401 — registers route handlers on the blueprint
