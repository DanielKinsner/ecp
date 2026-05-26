"""Image helpers for report embedding."""

import base64


def encode_image_base64(image_path):
    """Base64 encode an image file for data URI embedding."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")
