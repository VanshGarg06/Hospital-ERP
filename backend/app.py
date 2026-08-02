"""
This is the entry point for the Flask application. 
It imports the app instance from the app module and 
runs the application in debug mode when executed directly.
"""

from bandhan import app

if __name__ == "__main__":
    app.run(debug=True)
