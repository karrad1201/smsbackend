from fastapi import FastAPI, Request
from src.core.logging_config import get_logger
from fastapi.middleware.cors import CORSMiddleware
import time
from importlib.metadata import version

class Application():
    def __init__(self, lifespan):
        self.app = FastAPI(
            title="FastAPI REST Template",
            description="A FastAPI REST template",
            lifespan=lifespan,
            version=version("SMSROOMBackend"),
            redoc_url=None
        )
        self.logger = get_logger('Application')
        self._add_middlewares()
        self._add_cors_middleware()
        self.logger.info(f'Application initialized. Version: {version("SMSROOMBackend")}')

    def include_routers(self, routers: list):
        try:
            for router in routers:
                self.app.include_router(router)
            self.logger.info('Routers included')
        except Exception as e:
            self.logger.error(f"Error including routers: {e}")

    def _add_cors_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.logger.info("CORS middleware added")

    def _add_middlewares(self):
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()

            self.logger.info(f"Request: {request.method} {request.url}")

            response = await call_next(request)

            process_time = time.time() - start_time
            self.logger.info(
                f"Response: {response.status_code} "
                f"completed in {process_time:.4f}s"
            )

            return response