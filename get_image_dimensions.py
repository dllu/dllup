import requests
from PIL import Image
from io import BytesIO
import sqlite3


def is_url(path):
    """Check if the given path is a URL."""
    return path.startswith("http://") or path.startswith("https://")


def get_image_size(image_path):
    """Get the size of the image from a given path or URL."""
    if is_url(image_path):
        # Fetch the image from the URL
        response = requests.get(image_path)
        image = Image.open(BytesIO(response.content))
    else:
        # Open the local image file
        image = Image.open(image_path)
    return image.size


def get_image_dimensions(path, db_path="/tmp/img_size_db.db"):
    """Get the dimensions of an image from a URL or local path, with caching."""
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS image_cache
                      (path TEXT PRIMARY KEY, width INTEGER, height INTEGER)"""
    )

    # Check if the path is already in the cache
    cursor.execute("SELECT width, height FROM image_cache WHERE path = ?", (path,))
    result = cursor.fetchone()

    if result:
        # If the path is in the cache, return the cached dimensions
        width, height = result
        print(f"Retrieved from cache: Width = {width}, Height = {height}")
    else:
        # If the path is not in the cache, fetch the image and calculate its dimensions
        width, height = get_image_size(path)

        # Save the new dimensions to the cache
        cursor.execute(
            "INSERT INTO image_cache (path, width, height) VALUES (?, ?, ?)",
            (path, width, height),
        )
        conn.commit()
        print(f"Fetched and cached: Width = {width}, Height = {height}")

    # Close the database connection
    conn.close()
    return width, height
