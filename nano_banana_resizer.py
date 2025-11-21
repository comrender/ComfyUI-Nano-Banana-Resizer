"""
nano_banana_resizer.py

Nano Banana Size Calculator – NB1 + NB2 with fixed tier switching & exact matching
"""

from typing import Tuple

class NanoBananaSizeCalculator:
    # ──────────────────────────────────────────────────────────────
    # Nano Banana 1 – original ~1MP buckets (div 32)
    # Verified from testing, removing duplicates and unverified entries
    # ──────────────────────────────────────────────────────────────
    BUCKETS_NB1 = [
        (512, 2048),   # 1:4
        (576, 1792),   # 1:3.1
        (736, 1408),   # 1:1.91
        (768, 1344),   # 9:16
        (800, 1280),   # 5:8
        (832, 1248),   # 2:3
        (864, 1184),   # 3:4
        (896, 1152),   # 7:9
        (928, 1120),   # 5:6
        (960, 1088),   # 1:1.13
        (1024, 1024),  # 1:1
        (1088, 960),   # 1.13:1
        (1120, 928),   # 1.21:1
        (1152, 896),   # 1.29:1
        (1184, 864),   # 4:3
        (1248, 832),   # 3:2
        (1280, 800),   # 8:5
        (1344, 768),   # 16:9
        (1408, 736),   # 1.91:1
        (1472, 704),   # 2.09:1
        (1792, 576),   # 3.11:1
        (2048, 512),   # 4:1
    ]

    # ──────────────────────────────────────────────────────────────
    # Nano Banana 2 – dense buckets (all div 32)
    # ──────────────────────────────────────────────────────────────
    BUCKETS_NB2_1K = [
        (768, 1344), (800, 1280), (832, 1248), (864, 1184), (896, 1152),
        (928, 1120), (960, 1088), (992, 1056), (1024, 1024), (1056, 992),
        (1088, 960), (1120, 928), (1152, 896), (1184, 864), (1248, 832),
        (1280, 800), (1344, 768),
    ]

    BUCKETS_NB2_2K = [
        (1024, 4096), (1088, 3840), (1152, 3584), (1216, 3328), (1280, 3072),
        (1344, 2816), (1408, 2560), (1472, 2816), (1536, 2688), (1600, 2560),
        (1664, 2496), (1696, 2528), (1728, 2368), (1792, 2304), (1856, 2240),
        (1920, 2176), (1984, 2048), (2048, 2048), (2176, 1920), (2240, 1856),
        (2304, 1792), (2368, 1728), (2496, 1664), (2560, 1600), (2688, 1536),
        (2816, 1472), (3072, 1280), (3328, 1216), (3584, 1152), (3840, 1088),
        (4096, 1024),
    ]

    BUCKETS_NB2_4K = [
        (2048, 8192), (2176, 7680), (2304, 7168), (2432, 6656), (2560, 6144),
        (2688, 5632), (2816, 5120), (2944, 5632), (3072, 5376), (3200, 5120),
        (3328, 4992), (3392, 5056), (3456, 4736), (3584, 4608), (3712, 4480),
        (3840, 4352), (3968, 4096), (4096, 4096), (4352, 3840), (4480, 3712),
        (4608, 3584), (4736, 3456), (4992, 3328), (5120, 3200), (5376, 3072),
        (5632, 2944), (6144, 2560), (6656, 2432), (7168, 2304), (7680, 2176),
        (8192, 2048),
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "version": (["Nano Banana 1", "Nano Banana 2"], {"default": "Nano Banana 1"}),
            },
            "optional": {
                "resolution": (["Auto", "1K", "2K", "4K"], {
                    "default": "Auto",
                    "tooltip": "Force specific tier for Nano Banana 2"
                }),
            }
        }

    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("width", "height", "info")
    FUNCTION = "calculate_size"
    CATEGORY = "image/transform"

    def _closest_bucket(self, ar: float, buckets) -> Tuple[int, int]:
        """Find closest bucket by aspect ratio with no bias"""
        return min(buckets, key=lambda x: abs(x[0]/x[1] - ar))

    def _auto_tier(self, pixels: int, ar: float) -> str:
        """
        Automatically select resolution tier based on input pixels and aspect ratio.
        
        Logic:
        - >= 8MP: Always use 4K
        - >= 2MP: Use 4K for extreme aspect ratios (>2.5 or <0.4), otherwise 2K
        - >= 1MP: Use 2K for wide aspect ratios (>2.0 or <0.5), otherwise 1K
        - < 1MP: Always use 1K
        """
        if pixels >= 8_000_000:
            return "4K"
        if pixels >= 2_000_000:
            return "4K" if (ar > 2.5 or ar < 0.4) else "2K"
        if pixels >= 1_000_000:
            return "2K" if (ar > 2.0 or ar < 0.5) else "1K"
        return "1K"

    def calculate_size(self, image, version: str, resolution: str = "Auto"):
        """
        Calculate optimal output dimensions for Nano Banana models.
        
        Args:
            image: Input image tensor (batch, height, width, channels)
            version: "Nano Banana 1" or "Nano Banana 2"
            resolution: "Auto", "1K", "2K", or "4K" (only for NB2)
        
        Returns:
            tuple: (output_width, output_height, info_string)
        """
        # Get input dimensions from tensor
        # ComfyUI image format is (batch, height, width, channels)
        _, h, w, _ = image.shape
        ar = w / h
        pixels = w * h

        if version == "Nano Banana 1":
            w_out, h_out = self._closest_bucket(ar, self.BUCKETS_NB1)
            info = f"Nano Banana 1 • {w_out}×{h_out} • Input: {w}×{h}"

        else:  # Nano Banana 2
            if resolution == "Auto":
                tier = self._auto_tier(pixels, ar)
            else:
                tier = resolution
            
            buckets = {
                "1K": self.BUCKETS_NB2_1K,
                "2K": self.BUCKETS_NB2_2K,
                "4K": self.BUCKETS_NB2_4K,
            }[tier]
            
            w_out, h_out = self._closest_bucket(ar, buckets)
            info = f"Nano Banana 2 {tier} • {w_out}×{h_out} • Input: {w}×{h}"

        return (w_out, h_out, info)


NODE_CLASS_MAPPINGS = {"NanoBananaSizeCalculator": NanoBananaSizeCalculator}
NODE_DISPLAY_NAME_MAPPINGS = {"NanoBananaSizeCalculator": "Nano Banana Size Calculator"}
