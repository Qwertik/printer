def register_blueprints(app):
    from .v1 import v1_bp
    app.register_blueprint(v1_bp)
