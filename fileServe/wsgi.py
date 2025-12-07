import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app as application

if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=8002)