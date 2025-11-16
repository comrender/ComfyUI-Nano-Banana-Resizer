"""
nano_banana_resizer.py

ComfyUI Custom Node: Nano Banana Size Calculator
Automatically calculates optimal output dimensions for Google's Nano Banana (Imagen3)
based on input image size and aspect ratio.
"""

class NanoBananaSizeCalculator:
    """
    Calculates output dimensions for Nano Banana model which uses:
    - ~1MP target resolution
    - Divisor of 32 for dimensions
    - Aspect ratio bucketing
    """
    
    # Known aspect ratio buckets (portrait orientation, width×height)
    # All dimensions divisible by 32, targeting ~1MP
    BUCKETS = [
        (512, 2048),   # 0.25 (1:4)
        (576, 1792),   # 0.32 (1:3.1)
        (736, 1408),   # 0.52 (1:1.91)
        (768, 1344),   # 0.57 (9:16)
        (800, 1280),   # 0.625 (5:8)
        (832, 1248),   # 0.67 (2:3)
        (864, 1184),   # 0.73 (3:4)
        (896, 1152),   # 0.78 (7:9)
        (928, 1120),   # 0.83 (5:6)
        (960, 1088),   # 0.88 (1:1.13)
        (1024, 1024),  # 1.0 (1:1)
        (1088, 960),   # 1.13 (landscape)
        (1120, 928),   # 1.21 (landscape)
        (1152, 896),   # 1.29 (landscape)
        (1184, 864),   # 1.37 (4:3)
        (1248, 832),   # 1.5 (3:2)
        (1280, 800),   # 1.6 (8:5)
        (1344, 768),   # 1.75 (16:9)
        (1408, 736),   # 1.91 (landscape)
        (1472, 704),   # 2.09 (2:1)
        (1792, 576),   # 3.11 (3:1)
        (2048, 512),   # 4.0 (4:1)
    ]
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "calculate_size"
    CATEGORY = "image/transform"
    
    def calculate_size(self, image):
        """
        Calculate optimal output dimensions based on input image.
        
        Args:
            image: Input image tensor (batch, height, width, channels)
        
        Returns:
            tuple: (output_width, output_height)
        """
        # Get input dimensions from tensor
        # ComfyUI image format is (batch, height, width, channels)
        batch, input_height, input_width, channels = image.shape
        
        # Calculate aspect ratio
        aspect_ratio = input_width / input_height
        
        # Find closest bucket by aspect ratio
        output_width, output_height = self._find_closest_bucket(aspect_ratio)
        
        return (output_width, output_height)
    
    def _find_closest_bucket(self, aspect_ratio):
        """
        Find the closest aspect ratio bucket.
        
        Args:
            aspect_ratio: Target aspect ratio (width/height)
        
        Returns:
            tuple: (width, height) from bucket
        """
        closest_bucket = None
        min_difference = float('inf')
        
        for width, height in self.BUCKETS:
            bucket_aspect = width / height
            difference = abs(bucket_aspect - aspect_ratio)
            
            if difference < min_difference:
                min_difference = difference
                closest_bucket = (width, height)
        
        return closest_bucket


# Node registration mappings
NODE_CLASS_MAPPINGS = {
    "NanoBananaSizeCalculator": NanoBananaSizeCalculator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NanoBananaSizeCalculator": "Nano Banana Size Calculator"
}