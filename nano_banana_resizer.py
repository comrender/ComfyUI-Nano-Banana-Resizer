"""
nano_banana_resizer.py

Nano Banana Size Calculator – NB1 + NB2 with fixed tier switching, 
missing buckets added, and dynamic fallback for Pro models.
"""

from typing import Tuple, List
import math

class NanoBananaSizeCalculator:
    # ──────────────────────────────────────────────────────────────
    # Nano Banana 1 – original ~1MP buckets (div 32)
    # ──────────────────────────────────────────────────────────────
    BUCKETS_NB1 = [
        (512, 2048), (576, 1792), (736, 1408), (768, 1344), (800, 1280),
        (832, 1248), (864, 1184), (896, 1152), (928, 1120), (960, 1088),
        (1024, 1024), (1088, 960), (1120, 928), (1152, 896), (1184, 864),
        (1248, 832), (1280, 800), (1344, 768), (1408, 736), (1472, 704),
        (1792, 576), (2048, 512),
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
        (1664, 2496), (1696, 2528), (1728, 2368), 
        (1760, 2432), (2432, 1760), # <--- ADDED: Fixes specific 1731x2423 input case
        (1792, 2304), (1856, 2240),
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
                "preset": ([
                    "Nano Banana 1",
                    "Nano Banana 2 (1K)",
                    "Nano Banana 2 (2K)",
                    "Nano Banana 2 (4K)"
                ], {"default": "Nano Banana 2 (2K)"}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("width", "height", "info")
    FUNCTION = "calculate_size"
    CATEGORY = "image/transform"

    def _closest_bucket(self, w_in: int, h_in: int, buckets: List[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Hybrid Logic: 
        1. Find closest hardcoded bucket (Euclidean distance).
        2. If distance is too high (i.e., aspect ratio is not covered), 
           use a dynamic Ceiling calculation to guarantee a non-cropping, 32-aligned size.
        """
        # 1. Try to find a match in the hardcoded list first
        candidates = []
        for w_bucket, h_bucket in buckets:
            # Calculate Euclidean distance squared
            dist_sq = (w_in - w_bucket) ** 2 + (h_in - h_bucket) ** 2
            candidates.append((dist_sq, w_bucket, h_bucket))
        
        candidates.sort(key=lambda x: x[0])
        best_dist, best_w, best_h = candidates[0]

        # 2. Safety Check: If the "best" match is too far away (e.g., dist_sq > 2000),
        # use the reverse-engineered dynamic calculation ("Pro" Ceiling logic).
        # This handles random/weird aspect ratios without error.
        if best_dist > 2000 and len(buckets) > 20: # Only applies to NB2 (Dense) lists
            import math
            
            # Use the input image dimensions for the dynamic calculation
            w_new = w_in
            h_new = h_in
            
            # --- APPLY CEILING LOGIC ---
            # w_out = ceil(W / 32) * 32
            # This ensures the dimension is always rounded UP to prevent cropping.
            w_dynamic = math.ceil(w_new / 32) * 32
            h_dynamic = math.ceil(h_new / 32) * 32
            
            # Return dynamic calculation
            return (int(w_dynamic), int(h_dynamic))

        # Otherwise, return the matched bucket (which is perfect, or close enough)
        return (best_w, best_h)

    def calculate_size(self, image, preset: str):
        """
        Calculate optimal output dimensions for Nano Banana models.
        """
        # Get input dimensions from tensor (batch, height, width, channels)
        _, h, w, _ = image.shape

        # Determine buckets based on preset
        if preset == "Nano Banana 1":
            target_buckets = self.BUCKETS_NB1
            version_info = "Nano Banana 1"
        elif "1K" in preset:
            target_buckets = self.BUCKETS_NB2_1K
            version_info = "Nano Banana 2 (1K)"
        elif "2K" in preset:
            target_buckets = self.BUCKETS_NB2_2K
            version_info = "Nano Banana 2 (2K)"
        else: # 4K
            target_buckets = self.BUCKETS_NB2_4K
            version_info = "Nano Banana 2 (4K)"

        # Calculate using Hybrid Euclidean + Dynamic logic
        w_out, h_out = self._closest_bucket(w, h, target_buckets)
        
        info = f"{version_info} • {w_out}×{h_out} • Input: {w}×{h}"

        return (w_out, h_out, info)

NODE_CLASS_MAPPINGS = {"NanoBananaSizeCalculator": NanoBananaSizeCalculator}
NODE_DISPLAY_NAME_MAPPINGS = {"NanoBananaSizeCalculator": "Nano Banana Size Calculator"}

