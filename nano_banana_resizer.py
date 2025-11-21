"""
nano_banana_resizer.py

Nano Banana Size Calculator – NB1 + NB2 with fixed tier switching & Euclidean distance matching
"""

from typing import Tuple, List

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
                # Merged Version and Resolution to strictly control valid combinations
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
        Find closest bucket by Euclidean distance in pixel space.
        This matches buckets based on physical closeness rather than pure Aspect Ratio.
        
        Args:
            w_in: Input image width
            h_in: Input image height
            buckets: List of (width, height) tuples
        
        Returns:
            Closest bucket (width, height)
        """
        candidates = []
        for w_bucket, h_bucket in buckets:
            # Calculate Euclidean distance squared (no need for sqrt for comparison)
            # This effectively finds the bucket that requires the least stretching/cropping
            dist_sq = (w_in - w_bucket) ** 2 + (h_in - h_bucket) ** 2
            candidates.append((dist_sq, w_bucket, h_bucket))
        
        # Sort by smallest distance
        candidates.sort(key=lambda x: x[0])
        
        return (candidates[0][1], candidates[0][2])

    def calculate_size(self, image, preset: str):
        """
        Calculate optimal output dimensions for Nano Banana models.
        Args:
            image: Input image tensor (batch, height, width, channels)
            preset: Selected preset string
        
        Returns:
            tuple: (output_width, output_height, info_string)
        """
        # Get input dimensions from tensor
        # ComfyUI image format is (batch, height, width, channels)
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

        # Calculate using Euclidean distance logic (uses raw w/h instead of AR)
        w_out, h_out = self._closest_bucket(w, h, target_buckets)
        
        info = f"{version_info} • {w_out}×{h_out} • Input: {w}×{h}"

        return (w_out, h_out, info)


NODE_CLASS_MAPPINGS = {"NanoBananaSizeCalculator": NanoBananaSizeCalculator}
NODE_DISPLAY_NAME_MAPPINGS = {"NanoBananaSizeCalculator": "Nano Banana Size Calculator"}
