from PIL import Image, ImageFilter
import io


def preprocess_image(image_bytes_or_path, max_px: int = 2000) -> tuple[bytes, str]:
    if isinstance(image_bytes_or_path, (str, bytes)):
        img = Image.open(image_bytes_or_path)
    else:
        img = Image.open(io.BytesIO(image_bytes_or_path))
    img = img.convert("RGB")
    img.thumbnail((max_px, max_px), Image.LANCZOS)
    img = img.filter(ImageFilter.SHARPEN)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue(), "image/jpeg"


def pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> list[bytes]:
    from pdf2image import convert_from_bytes
    pages = convert_from_bytes(pdf_bytes, dpi=dpi)
    result = []
    for page in pages:
        buf = io.BytesIO()
        page.convert("RGB").save(buf, format="JPEG", quality=92)
        result.append(buf.getvalue())
    return result