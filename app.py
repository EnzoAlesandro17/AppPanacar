from src.app import create_app
from src.config import IS_PRODUCTION

app = create_app()

if __name__ == "__main__":
    app.run(debug=not IS_PRODUCTION)
