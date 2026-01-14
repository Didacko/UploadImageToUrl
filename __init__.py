
"""
ComfyUI custom node: comfyui-asset-to-url-0x0
Uploads IMAGE/AUDIO/FILE to 0x0.st and returns a direct URL (STRING).
"""

import io
import os
import wave
import requests
import numpy as np

try:
    import torch
except Exception:
    torch = None

try:
    from PIL import Image
except Exception:
    Image = None

CATEGORY = "I/O → URL"

def _upload_bytes(filename: str, data: bytes) -> str:
    r = requests.post("https://0x0.st", files={"file": (filename, data)}, timeout=120)
    r.raise_for_status()
    return r.text.strip()

class ImageToURL_0x0:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "format": (["png", "jpg"], {"default": "png"}),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = CATEGORY

    def run(self, image, format="png", quality=95):
        if Image is None:
            raise RuntimeError("Pillow (PIL) is required for ImageToURL_0x0")

        if torch is not None and isinstance(image, torch.Tensor):
            t = image
            if t.dim() == 4:
                t = t[0]
            arr = (t.clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)
        else:
            arr = (np.clip(image, 0, 1) * 255).astype(np.uint8)

        pil = Image.fromarray(arr)
        bio = io.BytesIO()
        if format.lower() == "png":
            pil.save(bio, format="PNG")
            filename = "image.png"
        else:
            pil.save(bio, format="JPEG", quality=int(quality))
            filename = "image.jpg"
        data = bio.getvalue()
        url = _upload_bytes(filename, data)
        return (url,)


class AudioToURL_0x0:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "filename": ("STRING", {"default": "audio.wav"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = CATEGORY

    def run(self, audio, filename="audio.wav"):
        if not isinstance(audio, dict) or "samples" not in audio or "sample_rate" not in audio:
            raise RuntimeError("AudioToURL_0x0 expects an AUDIO object with 'samples' and 'sample_rate'")

        samples = audio["samples"]
        sr = int(audio["sample_rate"])

        if torch is not None and isinstance(samples, torch.Tensor):
            arr = samples.detach().cpu().numpy()
        else:
            arr = np.asarray(samples)

        if arr.ndim == 1:
            arr = arr[np.newaxis, :]

        channels = arr.shape[0]
        arr = np.clip(arr, -1.0, 1.0)
        pcm = (arr.T * 32767.0).astype(np.int16)

        bio = io.BytesIO()
        with wave.open(bio, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(pcm.tobytes(order="C"))
        data = bio.getvalue()
        url = _upload_bytes(filename if filename.strip() else "audio.wav", data)
        return (url,)


class PathToURL_0x0:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = CATEGORY

    def run(self, path):
        p = str(path)
        if not os.path.isfile(p):
            raise RuntimeError(f"Path does not exist or is not a file: {p}")
        with open(p, "rb") as f:
            data = f.read()
        url = _upload_bytes(os.path.basename(p), data)
        return (url,)


NODE_CLASS_MAPPINGS = {
    "ImageToURL_0x0": ImageToURL_0x0,
    "AudioToURL_0x0": AudioToURL_0x0,
    "PathToURL_0x0": PathToURL_0x0,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageToURL_0x0": "Image → URL (0x0.st)",
    "AudioToURL_0x0": "Audio → URL (0x0.st)",
    "PathToURL_0x0": "Path → URL (0x0.st)",
}
