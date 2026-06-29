"""
Detect GPU, VRAM, RAM and classify hardware tier for Ollama inference.

``check_ollama_requirements()`` returns a dict with tier classification:
``"good"``, ``"marginal"``, or ``"cpu_only"`` along with human-readable
messages shown to the user before a local scan.
"""
import psutil
import requests


def check_ollama_requirements() -> dict:
    result = {
        "ollama_running": False,
        "vram_gb": 0.0,
        "ram_gb": 0.0,
        "gpu_name": "None detected",
        "tier": "none",
        "message": "",
    }

    try:
        result["ram_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except Exception:
        result["ram_gb"] = 0.0

    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        result["ollama_running"] = r.status_code == 200
    except Exception:
        pass

    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            result["gpu_name"] = gpus[0].name
            result["vram_gb"] = round(gpus[0].memoryTotal / 1024, 1)
    except Exception:
        # No GPU, no drivers, GPUtil/nvidia-smi missing, or anything else —
        # treat as "no GPU detected" rather than letting this bubble up.
        pass

    vram = result["vram_gb"]
    ram = result["ram_gb"]
    low_ram_warning = (
        "\n\n⚠ Warning: Your system RAM may be too low for stable CPU inference."
        if 0 < ram < 16 else ""
    )

    if vram >= 8:
        result["tier"] = "good"
        result["message"] = (
            f"GPU: {result['gpu_name']} ({vram} GB VRAM)\n"
            "Your GPU meets the recommended requirements.\n"
            "Ollama will run at full GPU speed — expect 10–30 seconds per image."
        )
    elif vram >= 4:
        result["tier"] = "marginal"
        result["message"] = (
            f"GPU: {result['gpu_name']} ({vram} GB VRAM)\n"
            "Your GPU has less than 8 GB VRAM. Some model layers will offload to RAM.\n"
            "Expect 2–5 minutes per image."
        )
    elif 0 < vram < 4:
        result["tier"] = "cpu_only"
        result["message"] = (
            f"GPU: {result['gpu_name']} ({vram} GB VRAM) — too little VRAM.\n\n"
            f"The minimum VRAM to use GPU acceleration is 8 GB.\n"
            f"Your GPU ({result['gpu_name']}) only has {vram} GB, so Ollama will ignore it "
            f"and run on CPU instead.\n\n"
            f"System RAM: {ram} GB (minimum 16 GB needed for CPU mode)\n"
            f"Expected time per image: 5–15 minutes on CPU."
            + low_ram_warning
        )
    else:
        result["tier"] = "cpu_only"
        result["message"] = (
            "No GPU detected.\n\n"
            "Ollama will run in CPU-only mode.\n"
            f"System RAM: {ram} GB (minimum 16 GB needed)\n"
            "Expected time per image: 5–15 minutes."
            + low_ram_warning
        )
    return result