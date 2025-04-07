import pytest
import sys
import os

# Add the backend directory to the sys.path to ensure correct imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Now import the app
from app import app as flask_app # Import your Flask app instance

@pytest.fixture(scope='module')
def app():
    """Instance of Flask app"""
    # Configure app for testing if necessary (e.g., different DB)
    # flask_app.config.update({
    #     "TESTING": True,
    #     "MONGO_URI": "mongodb://localhost:27017/linkedin_style_sync_test" # Example: Use a test DB
    # })

    # TODO: Potentially mock external API calls (Anthropic, Brave) here
    # using pytest-mock or unittest.mock if you don't want tests hitting live APIs.

    yield flask_app

# Removed the client fixture as pytest-flask provides it automatically when app is defined.
# pytest-flask automatically provides a `client` fixture based on the `app` fixture.
