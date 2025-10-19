from src.core.app import Application
from src.presentation.api import routers
from src.core.logging_config import setup_logging, get_logger
from contextlib import asynccontextmanager
from sqlalchemy.exc import OperationalError
import sys

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app):
    order_service = None
    try:
        from src.infrastructure.database.init_db import sync_database
        await sync_database()
        logger.info("✅ Database connection established")

        from src.core.di.service import get_order_service
        order_service = get_order_service()
        await order_service.start_background_tasks()
        logger.info("✅ Background tasks started")

        yield

    except OperationalError as e:
        logger.error(f"Database error: {e}")
        yield
        sys.exit()
    except Exception as e:
        logger.error(f"Error in lifespan: {e}")
        yield
        sys.exit()
    finally:
        if order_service:
            await order_service.stop_background_tasks()
            logger.info("✅ Background tasks stopped")
        logger.info("Database connection closed")


application = Application(lifespan=lifespan)
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
    finally:
        logger.info("Server stopped")