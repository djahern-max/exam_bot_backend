import os
import uuid
from PIL import Image
import io
from typing import Optional, Tuple, BinaryIO

# First, register the HEIF opener with Pillow
try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False
    print("Warning: pillow_heif not installed. HEIC files will not be supported.")


def convert_heic_to_png(image_data: bytes) -> bytes:
    """
    Convert HEIC image data to PNG format.

    Args:
        image_data: Binary image data

    Returns:
        Converted PNG image data
    """
    try:
        # Open the image from binary data
        image = Image.open(io.BytesIO(image_data))

        # Convert and save as PNG
        output = io.BytesIO()
        image.save(output, format="PNG")
        output.seek(0)

        return output.getvalue()
    except Exception as e:
        raise Exception(f"Error converting HEIC to PNG: {str(e)}")


def process_image_file(file: BinaryIO, original_filename: str) -> Tuple[str, bytes]:
    """
    Process an uploaded image file, handling different formats including HEIC.

    Args:
        file: The uploaded file object
        original_filename: Original filename

    Returns:
        Tuple of (processed_content, file_extension)
    """
    file_content = file.read()
    file_extension = os.path.splitext(original_filename)[1].lower()

    # Handle HEIC files from iPhones
    if file_extension in [".heic", ".heif"] and HEIF_SUPPORT:
        print(f"Converting HEIC file to PNG: {original_filename}")
        file_content = convert_heic_to_png(file_content)
        file_extension = ".png"

    return file_content, file_extension


def save_uploaded_image(
    file: BinaryIO, original_filename: str, upload_dir: str = "uploads"
) -> str:
    """
    Save an uploaded image file, handling different formats including HEIC.

    Args:
        file: The uploaded file object
        original_filename: Original filename
        upload_dir: Directory to save the image

    Returns:
        Path to the saved image file
    """
    # Create upload directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)

    # Process the file
    file_content, file_extension = process_image_file(file, original_filename)

    # Generate a unique filename
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(upload_dir, filename)

    # Save the file
    with open(file_path, "wb") as f:
        f.write(file_content)

    return file_path
