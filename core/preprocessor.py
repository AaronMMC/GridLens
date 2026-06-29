"""
Image preprocessing and PDF-to-image conversion.

``preprocess_image()`` resizes, sharpens, and re-encodes an image as JPEG
for upload to AI backends.  ``pdf_to_images()`` rasterises each PDF page
to JPEG bytes.
"""
from PIL import Image, ImageFilter
import io


def preprocess_image(image_bytes_or_path, max_px: int = 2000) -> tuple[bytes, str]:
    """Returns (jpeg_bytes, 'image/jpeg'). Accepts a file path (str/Path)
    OR raw image bytes.

    BUGFIX: the original version did
        if isinstance(image_bytes_or_path, (str, bytes)):
            img = Image.open(image_bytes_or_path)
    which calls Image.open() directly on raw `bytes`. PIL's Image.open()
    only accepts a filename/Path or a file-like object with .read() —
    not a bare bytes object — so this raised AttributeError on every
    single scan, since the app always calls this with bytes (read from
    disk or produced by pdf_to_images()), never a path. That crash
    happened before any backend was even chosen, which is why it looked
    like "scanning crashes" regardless of which backend was active.
    """
    if isinstance(image_bytes_or_path, (bytes, bytearray)):
        img = Image.open(io.BytesIO(image_bytes_or_path))
    else:
        img = Image.open(image_bytes_or_path)
    img = img.convert("RGB")
    img.thumbnail((max_px, max_px), Image.LANCZOS)
    img = img.filter(ImageFilter.SHARPEN)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue(), "image/jpeg"


def pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> list[bytes]:
    """Convert each PDF page to JPEG bytes, one entry per page."""
    from pdf2image import convert_from_bytes
    pages = convert_from_bytes(pdf_bytes, dpi=dpi)
    result = []
    for page in pages:
        buf = io.BytesIO()
        page.convert("RGB").save(buf, format="JPEG", quality=92)
        result.append(buf.getvalue())
    return result