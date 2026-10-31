"""Local launcher. Use a single Waitress process for a non-debug server."""

import os
from app.main import create_app

if __name__ == "__main__":
    create_app().run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=False,
        use_reloader=False,
    )
