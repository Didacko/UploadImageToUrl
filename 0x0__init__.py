import os, io, re, base64, wave, requests

try:
    import torch
except Exception:
    torch = None

try:
    import numpy as np
except Exception:
    np = None


# ============ helpers de red ============

def _ensure_https(url: str) -> str:
    if url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url

def _verify_accessible(url: str, timeout: int = 20) -> bool:
    try:
        h = requests.head(url, allow_redirects=True, timeout=timeout)
        if 200 <= h.status_code < 300:
            return True
        if h.status_code in (403, 405):
            g = requests.get(url, stream=True, allow_redirects=True, timeout=timeout)
            ok = 200 <= g.status_code < 300
            try:
                next(g.iter_content(chunk_size=1))
            except Exception:
                pass
            g.close()
            return ok
        return False
    except Exception:
        return False


# ============ uploaders individuales ============

def _upload_0x0(filename: str, data: bytes) -> str:
    r = requests.post("https://0x0.st", files={"file": (filename, data)},
                      timeout=60, headers={"User-Agent": "curl/8.0"})
    r.raise_for_status()
    return _ensure_https(r.text.strip())

def _upload_transfer_sh(filename: str, data: bytes) -> str:
    r = requests.put(f"https://transfer.sh/{filename}", data=data,
                     timeout=120, headers={"User-Agent": "curl/8.0"})
    r.raise_for_status()
    return _ensure_https(r.text.strip().split()[0])

def _upload_catbox(filename: str, data: bytes) -> str:
    r = requests.post("https://catbox.moe/user/api.php",
                      data={"reqtype": "fileupload"},
                      files={"fileToUpload": (filename, data)},
                      timeout=120)
    r.raise_for_status()
    url = r.text.strip()
    return "https://files.catbox.moe/" + url.split("/")[-1] if not url.startswith("http") else url

def _upload_litterbox(filename: str, data: bytes, expire_time: str = "1h") -> str:
    if expire_time not in {"1h", "12h", "24h", "72h", ""}:
        expire_time = "1h"
    payload = {"reqtype": "fileupload"}
    if expire_time:
        payload["time"] = expire_time
    r = requests.post("https://litterbox.catbox.moe/resources/internals/api.php",
                      data=payload,
                      files={"fileToUpload": (filename, data)},
                      timeout=120)
    r.raise_for_status()
    return r.text.strip()

def _upload_pixeldrain(filename: str, data: bytes) -> str:
    # Pixeldrain permite anónimo con PUT
    r = requests.put("https://pixeldrain.com/api/file/" + filename,
                     data=data,
                     timeout=180)
    r.raise_for_status()
    file_id = r.json()["id"]
    return f"https://pixeldrain.com/u/{file_id}"


# ============ upload con fallback ============

def _upload_bytes(filename: str, data: bytes, uploader: str = "auto", expire_time: str = "1h") -> str:
    order = {
        "auto":       (_upload_catbox, _upload_litterbox, _upload_pixeldrain, _upload_0x0, _upload_transfer_sh),
        "catbox":     (_upload_catbox,),
        "litterbox":  (_upload_litterbox,),
        "pixeldrain": (_upload_pixeldrain,),
        "0x0":        (_upload_0x0,),
        "transfer.sh":(_upload_transfer_sh,),
    }.get(uploader.lower(), (_upload_catbox,))

    last = None
    for fn in order:
        try:
            if fn is _upload_litterbox:
                url = fn(filename, data, expire_time=expire_time)
            else:
                url = fn(filename, data)
            url = _ensure_https(url)
            if _verify_accessible(url):
                return url
            last = RuntimeError(f"uploaded but not accessible: {url}")
        except Exception as e:
            last = e
            continue
    raise last if last else RuntimeError("upload failed")


# ============ resto del código (sin cambios) ============

# ... (todo el código de _img_to_bytes, _samples_to_wav, etc. queda exactamente igual)

class ImageToURL_0x0:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "image_format": (["png", "jpeg", "webp"], {"default": "png"}),
                "jpeg_quality": ("INT", {"default": 95, "min": 1, "max": 100}),
                "filename_hint": ("STRING", {"default": "image.png"}),
                "uploader": (["auto", "catbox", "litterbox", "pixeldrain", "0x0", "transfer.sh"], {"default": "auto"}),
            },
            "optional": {
                "expire_time": ("STRING", {"default": "1h", "tooltip": "Solo usado si uploader=litterbox. Valores: 1h,12h,24h,72h o vacío"})
            }
        }
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("url",)
    FUNCTION = "run"
    CATEGORY = "I/O → URL"

    def run(self, image, image_format="png", jpeg_quality=95, filename_hint="image.png",
            uploader="auto", expire_time="1h"):
        data = _img_to_bytes(image, fmt=image_format, quality=jpeg_quality)
        ext = {"png": "png", "jpeg": "jpg", "webp": "webp"}[image_format]
        fn = filename_hint.strip() or f"image.{ext}"
        if not fn.lower().endswith(f".{ext}"):
            fn = f"{fn}.{ext}"
        url = _upload_bytes(fn, data, uploader=uploader, expire_time=expire_time)
        return (_ensure_https(url),)

# El resto de clases (AudioToURL_0x0 y PathToURL_0x0) puedes dejarlas igual o adaptarlas si quieres.

NODE_CLASS_MAPPINGS = {
    "ImageToURL_0x0": ImageToURL_0x0,
    "AudioToURL_0x0": AudioToURL_0x0,
    "PathToURL_0x0": PathToURL_0x0,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageToURL_0x0": "Image → URL (multi-uploader)",
    "AudioToURL_0x0": "Audio → URL (multi-uploader)",
    "PathToURL_0x0": "Path → URL (multi-uploader)",
}