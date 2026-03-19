import os
import sys
from pathlib import Path
from app import create_app, db

environment = os.getenv('ENVIRONMENT', 'production')
app = create_app(environment)

@app.shell_context_processor
def make_shell_context():
    return {'db': db}

if __name__ == '__main__':
    app.run()