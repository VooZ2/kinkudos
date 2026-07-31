import warnings
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()

SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "HEIF", "HEIC"}
MAX_IMAGE_PIXELS = 40_000_000


class ImageProcessingError(ValueError):
    pass


@dataclass(frozen=True)
class ProcessedEvidence:
    image: bytes
    thumbnail: bytes


def _open_image(upload):
    try:
        upload.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(upload)
            image_format = (image.format or "").upper()
            if image_format not in SUPPORTED_IMAGE_FORMATS:
                raise ImageProcessingError("unsupported-format")
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ImageProcessingError("too-many-pixels")
            image.load()
        return ImageOps.exif_transpose(image)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ImageProcessingError("too-many-pixels") from None
    except ImageProcessingError:
        raise
    except (OSError, SyntaxError, ValueError):
        raise ImageProcessingError("invalid-image") from None


def _flatten_to_rgb(image):
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        background.alpha_composite(rgba)
        return background.convert("RGB")
    return image.convert("RGB")


def _webp_bytes(image, *, quality=82):
    output = BytesIO()
    image.save(output, format="WEBP", quality=quality, method=6, exif=b"")
    return output.getvalue()


def process_avatar(upload):
    image = _flatten_to_rgb(_open_image(upload))
    image = ImageOps.fit(image, (512, 512), method=Image.Resampling.LANCZOS)
    return _webp_bytes(image, quality=88)


def process_task_evidence(upload):
    image = _flatten_to_rgb(_open_image(upload))
    image.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
    thumbnail = image.copy()
    thumbnail.thumbnail((320, 320), Image.Resampling.LANCZOS)
    return ProcessedEvidence(
        image=_webp_bytes(image, quality=82),
        thumbnail=_webp_bytes(thumbnail, quality=78),
    )


def process_feedback_screenshot(upload):
    image = _flatten_to_rgb(_open_image(upload))
    image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    return _webp_bytes(image, quality=82)
