from src.core.app import Application
from src.presentation.api import routers
from src.core.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

application = Application()
app = application.app
application.include_routers(routers)


if __name__ == '__main__':
    import uvicorn
    try:
        uvicorn.run(app, host='0.0.0.0', port=8000)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")