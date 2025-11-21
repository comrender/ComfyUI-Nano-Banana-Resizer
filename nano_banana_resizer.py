"""
nano_banana_resizer.py

ComfyUI Custom Node: Nano Banana Size Calculator (NB1 + NB2)
Supports Nano Banana 1 (~1MP) and Nano Banana 2 (1K/2K/4K) with divisor 32.
"""

from typing import Tuple

class NanoBananaSizeCalculator:
    """
    Unified calculator for Nano Banana 1 and 2 with expanded buckets for accuracy.
    """

    # Nano Banana 1: Original ~1MP buckets (div by 32)
    BUCKETS_NB1 = [
        (512, 2048), (544, 1920), (576, 1792), (608, 1664), (640, 1536), (672, 1408),
        (704, 1280), (736, 1408), (768, 1344), (800, 1280), (832, 1248), (864, 1184),
        (896, 1152), (928, 1120), (960, 1088), (992, 1024), (1024, 1024),
        (1024, 992), (1088, 960), (1120, 928), (1152, 896), (1184, 864),
        (1248, 832), (1280, 800), (1344, 768), (1408, 736), (1536, 640),
        (1664, 608), (1792, 576), (1920, 544), (2048, 512),
    ]

    # Nano Banana 2: Expanded buckets (div by 32), scaled from NB1
    BUCKETS_NB2_1K = [  # ~1K: x1 scale + fills
        (768, 1344), (800, 1280), (832, 1248), (864, 1184), (896, 1152),
        (928, 1120), (960, 1088), (992, 1056), (1024, 1024), (1056, 992),
        (1088, 960), (1120, 928), (1152, 896), (1184, 864), (1248, 832),
        (1280, 800), (1344, 768),
    ]
    BUCKETS_NB2_2K = [  # ~2K: x2 scale + fills (includes 1696x2528)
        (1024, 4096), (1088, 3840), (1152, 3584), (1216, 3328), (1280, 3072),
        (1344, 2816), (1408, 2560), (1472, 2816), (1536, 2688), (1600, 2560),
        (1664, 2496), (1696, 2528), (1728, 2368), (1792, 2304), (1856, 2240),
        (1920, 2176), (1984, 2048), (2048, 2048), (2048, 1984), (2176, 1920),
        (2240, 1856), (2304, 1792), (2368, 1728), (2496, 1664), (2560, 1600),
        (2688, 1536), (2816, 1472), (3072, 1280), (3328, 1216), (3584, 1152),
        (3840, 1088), (4096, 1024),
    ]
    BUCKETS_NB2_4K = [  # ~4K: x4 scale + fills
        (2048, 8192), (2176, 7680), (2304, 7168), (2432, 6656), (2560, 6144),
        (2688, 5632), (2816, 5120), (2944, 5632), (3072, 5376), (3200, 5120),
        (3328, 4992), (3392, 5056), (3456, 4736), (3584, 4608), (3712, 4480),
        (3840, 4352), (3968, 4096), (4096, 4096), (4096, 3968), (4352, 3840),
        (4480, 3712), (4608, 3584), (4736, 3456), (4992, 3328), (5120, 3200),
        (5376, 3072), (5632, 2944), (6144, 2560), (6656, 2432), (7168, 2304),
        (7680, 2176), (8192, 2048),
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "version": (["Nano Banana 1", "Nano Banana 2"], {
                    "default": "Nano Banana 1"
                }),
            },
            "optional": {
                "resolution": (["Auto", "1K", "2K", "4K"], {
                    "default": "Auto",
                    "tooltip": "Force resolution tier for Nano Banana 2."
                }),
            }
        }

    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("width", "height", "info")
    FUNCTION = "calculate_size"
    CATEGORY = "image/transform"

    def _find_closest_bucket(self, aspect_ratio: float, buckets) -> Tuple[int, int]:
        closest = min(
            buckets,
            key=lambda wh: abs((wh[0] / wh[1]) - aspect_ratio)
        )
        return closest

    def _select_nb2_tier(self, input_pixels: int, aspect_ratio: float):
        if input_pixels >= 8_000_000:
            return "4K"
        elif input_pixels >= 2_000_000:
            if aspect_ratio > 2.5 or aspect_ratio < 0.4:
                return "4K"
            return "2K"
        else:
            return "1K"

    def calculate_size(self, image, version: str, resolution: str = "Auto"):
        batch, h, w, c = image.shape
        input_aspect = w / h
        input_pixels = w * h

        if version == "Nano Banana 1":
            width, height = self._find_closest_bucket(input_aspect, self.BUCKETS_NB1)
            info = f"Nano Banana 1 • {width}×{height}"

        else:  # Nano Banana 2
            if resolution != "Auto":
                tier = resolution
            else:
                tier = self._select_nb2_tier(input_pixels, input_aspect)

            if tier == "1K":
                buckets = self.BUCKETS_NB2_1K
            elif tier == "2K":
                buckets = self.BUCKETS_NB2_2K
            else:  # 4K
                buckets = self.BUCKETS_NB2_4K

            width, height = self._find_closest_bucket(input_aspect, buckets)
            info = f"Nano Banana 2 {tier} • {width}×{height}"

        return (width, height, info)


# Node registration mappings
NODE_CLASS_MAPPINGS = {
    "NanoBananaSizeCalculator": NanoBananaSizeCalculator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NanoBananaSizeCalculator": "Nano Banana Size Calculator"
}
