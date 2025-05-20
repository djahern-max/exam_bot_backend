import os
import uuid
from PIL import Image
from io import BytesIO
from typing import Optional, Tuple


def compress_image(image_bytes: bytes, max_size_mb: float = 1.0) -> bytes:
    """
    Compress an image to reduce its file size.
    
    Args:
        image_bytes: The original image bytes
        max_size_mb: The maximum size in MB
        
    Returns:
        Compressed image bytes
    """
    # Convert bytes to image
    img = Image.open(BytesIO(image_bytes))
    
    # Convert to RGB if mode is RGBA (removes alpha channel)
    if img.mode == "RGBA":
        img = img.convert("RGB")
    
    # Initial quality
    quality = 85
    output = BytesIO()
    img.save(output, format="JPEG", quality=quality)
    
    # Check size and compress further if needed
    max_size_bytes = max_size_mb * 1024 * 1024
    while output.tell() > max_size_bytes and quality > 10:
        quality -= 5
        output = BytesIO()
        img.save(output, format="JPEG", quality=quality)
    
    return output.getvalue()


def save_uploaded_image(content: bytes, filename: Optional[str] = None, upload_dir: str = "uploads") -> Tuple[str, str]:
    """
    Save an uploaded image to disk.
    
    Args:
        content: The image content
        filename: Original filename (optional)
        upload_dir: Directory to save the image
        
    Returns:
        Tuple of (file_path, filename)
    """
    # Create upload directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename if not provided
    if not filename:
        ext = ".jpg"
        filename = f"{uuid.uuid4()}{ext}"
    else:
        # Extract extension from filename
        _, ext = os.path.splitext(filename)
        # Generate a unique filename but keep the extension
        filename = f"{uuid.uuid4()}{ext}"
    
    # Build the file path
    file_path = os.path.join(upload_dir, filename)
    
    # Compress image if it's too large
    compressed_content = compress_image(content)
    
    # Save the image
    with open(file_path, "wb") as f:
        f.write(compressed_content)
    
    return file_path, filename