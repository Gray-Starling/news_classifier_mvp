import asyncio
from app.run_scrapper_periodically import run_scrapper_periodically
from utils.prelaunch_check import prelaunch_check

if __name__ == "__main__":    
    
    if not prelaunch_check():
        exit(1)
    
    asyncio.run(run_scrapper_periodically())