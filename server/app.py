# Entrypoint shim to satisfy the automated hackathon structural validator
import sys
import os

# Ensure the root directory is in the Python path
sys.path.insert(0, os.getcwd())

# Import the actual ASGI application from our module
from chip_floorplanner.server.app import app
import uvicorn

def main():
    port = int(os.getenv("PORT", 7860))
    # Run the Uvicorn server using our imported app
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
