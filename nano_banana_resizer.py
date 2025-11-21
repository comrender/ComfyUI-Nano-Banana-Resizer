"""
nano_banana_resizer.py

ComfyUI Custom Node: Nano Banana Resizer (v1 + v2 Support)
Supports both Nano Banana 1 (~1MP) and Nano Banana 2 (1K/2K/4K tiers)
Automatically selects optimal resolution bucket based on input image aspect ratio.
"""

from typing import Tuple

class NanoBananaResizer:
    """
    Unified resizer for Nano Banana 1 and Nano Banana 2
    """

    # Nano Banana 1: ~1MP buckets (divisible by 32)
    BUCKETS_NB1 = [
        (512, 2048), (576, 1792), (736, 1408), (768, 1344), (800, 1280),
        (832, 1248), (864, 1184), (896, 1152), (928, 1120), (960, 1088),
        (1024, 1024),
        (1088, 960), (1120, 928), (1152, 896), (1184, 864), (1248, 832),
        (1280, 800), (1344, 768), (1408, 736), (1472, 704), (1792, 576), (2048, 512),
    ]

    # Nano Banana 2: Multi-tier buckets (all divisible by 64)
    BUCKETS_NB2_1K = [   # ~1K tier: 1024–2048 range
        (768, 1344), (832, 1248), (896, 1152), (960, 1088), (1024, 1024),
        (1088, 960), (1152, 896), (1248, 832), (1344, 768),
    ]
    BUCKETS_NB2_2K = [   # ~2K tier: scaled x2 from good 1MP buckets → ~4MP
        (1024, 4096), (1152, 3584), (1472, 2816), (1536, 2688), (1600, 2560),
        (1664, 2496), (1728, 2368), (1792, 2304), (1856, 2240), (1920, 2176),
        (2048, 2048),
        (2176, 1920), (2240, 1856), (2304, 1792), (2368, 1728), (2496, 1664),
        (2560, 1600), (2688, 1536), (2816, 1472), (3584, 1152), (4096, 1024),
    ]
    BUCKETS_NB2_4K = [   # ~4K tier: scaled x4 → ~16MP
        (2048, 8192), (2304, 7168), (2944, 5632), (3072, 5376), (3200, 5120),
        (3328, 4992), (3456, 4736), (3584, 4608), (3712, 4480), (3840, 4352),
        (4096, 4096),
        (4352, 3840), (4480, 3712), (4608, 3584), (4736, 3456), (4992, 3328),
        (5120, 3200), (5376, 3072), (5632, 2944), (7168, 2304), (8192, 2048),
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "version": (["Nano Banana 1 (~1MP)", "Nano Banana 2 (1K/2K/4K auto)"], {
                    "default": "Nano Banana 1 (~1MP)"
                }),
            },
            "optional": {
                "force_tier_NB2": (["Auto", "1K (~1-2MP)", "2K (~4MP)", "4K (~16MP)"], {
                    "default": "Auto",
                    "tooltip": "Force specific resolution tier for Nano Banana 2. 'Auto' chooses best based on input size."
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
        """Auto-select best tier for Nano Banana 2"""
        if input_pixels >= 8_000_000:  # 4K+ input → go big
            return "4K"
        elif input_pixels >= 2_000_000:  # 2K+ input → prefer 2K or 4K
            # If very wide/narrow, 4K helps preserve detail
            if aspect_ratio > 2.5 or aspect_ratio < 0.4:
                return "4K"
            return "2K"
        else:
            return "1K"

    def calculate_size(self, image, version: str, force_tier_NB2: str = "Auto"):
        batch, h, w, c = image.shape
        input_aspect = w / h
        input_pixels = w * h

        if version == "Nano Banana 1 (~1MP)":
            width, height = self._find_closest_bucket(input_aspect, self.BUCKETS_NB1)
            info = f"Nano Banana 1 • {width}×{height} • {width*height//1000}K pixels"

        else:  # Nano Banana 2
            if force_tier_NB2 != "Auto":
                tier = force_tier_NB2.split()[0]  # "1K", "2K", "4K"
            else:
                tier = self._select_nb2_tier(input_pixels, input_aspect)

            if tier == "1K":
                buckets = self.BUCKETS_NB2_1K
                base = "~1K"
            elif tier == "2K":
                buckets = self.BUCKETS_NB2_2K
                base = "~2K"
            else:  # 4K
                buckets = self.BUCKETS_NB2_4K
                base = "~4K"

            width, height = self._find_closest_bucket(input_aspect, buckets)
            megapixels = width * height / 1_000_000
            info = f"Nano Banana 2 {tier} • {width}×{height} • {megapixels:.1f}MP"

        return (width, height, info)


# Node registration
NODE_CLASS_MAPPINGS = {
    "NanoBananaResizer": NanoBananaResizer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NanoBananaResizer": "Nano Banana Resizer (NB1 & NB2)"
}