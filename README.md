# comfyui-asset-to-url-0x0

Small ComfyUI custom node that uploads IMAGE/AUDIO/FILE to **0x0.st** and returns a direct URL.

## Install (Desktop / Node Manager)

1. ComfyUI → Manager → **Install via Git URL**  
2. Paste repo URL.  
3. Restart ComfyUI.

## Install (Comfy Deploy)

Project → **Custom Nodes** → add Git repo URL (optionally pin `@commit`).

## Nodes

- **Image → URL (0x0.st)** → input: IMAGE, output: STRING
- **Audio → URL (0x0.st)** → input: AUDIO, output: STRING (WAV)
- **Path → URL (0x0.st)** → input: STRING path, output: STRING

## Requirements
`requests`, `numpy`, `Pillow`

