import asyncio
from app.periodic_model_training import periodic_model_training
from settings.logger_setup import system_logger

if __name__ == "__main__":
    system_logger.info("Starting classification server")
    asyncio.run(periodic_model_training())