from config import NEWS_DATA_API
import os
import aiohttp

async def download_data(file_path):
    link = NEWS_DATA_API
    
    if os.path.exists(file_path):
        print(f"The file already exists: {file_path}")
        return
    else:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(link) as response:
                    if response.status == 200:
                        total_size = int(response.headers.get('Content-Length', 0))
                        downloaded_size = 0

                        with open(file_path, 'wb') as f:
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    print(f"\nThe file has been successfully downloaded and saved to the path: {file_path}")
                                    break
                                f.write(chunk)
                                downloaded_size += len(chunk)

                                if total_size > 0:
                                    print(f"Downloaded {downloaded_size} of {total_size} bytes", end='\r')
                    else:
                        print(f"Error loading. Status code: {response.status}")
        except Exception as e:
            print("Something went wrong while trying to upload the file:", e)
            raise e
