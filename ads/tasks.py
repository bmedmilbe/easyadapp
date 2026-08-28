import os
from io import BytesIO

from celery import shared_task
from django.core.files.base import ContentFile
from PIL import Image

from ads.models import TemporaryAdImage


@shared_task(name="process_temp_picture_task")
def process_temp_picture_task(image_id):
    """
    Asynchronously processes a temporary advertisement image.
    
    Resizes the image to a standard 1200x1200px canvas, pads it with a white 
    background if necessary, and converts the output to optimized WebP format.
    """
    try:
       
        instance = TemporaryAdImage.objects.get(id=image_id)
        
        # 'with' context manager ensures the Django file closes automatically
        with instance.image.open() as script_image:
            script_image.seek(0)
            image_bytes = BytesIO(script_image.read())
        
        # 'with' context manager manages the Pillow (PIL) image lifetime
        with Image.open(image_bytes) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Dimensions & Padding configuration
            target_size = (1200, 1200)
            canvas = Image.new("RGB", target_size, (255, 255, 255))
            
            # Downscale safely without altering small images
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Center the image on the 1200x1200px canvas
            offset = (
                (target_size[0] - img.size[0]) // 2,
                (target_size[1] - img.size[1]) // 2,
            )
            canvas.paste(img, offset)
            
            # Save optimized canvas to memory buffer
            buffer = BytesIO()
            canvas.save(buffer, format="WEBP", quality=85, optimize=True)
            buffer.seek(0)
            
            # Clean filename extraction
            raw_filename = os.path.basename(instance.image.name)
            name_without_ext, _ = os.path.splitext(raw_filename)
            
            # Assign to the field without triggering an early database save
            instance.api_image_webp.save(
                f"{name_without_ext}_api.webp", 
                ContentFile(buffer.read()), 
                save=False
            )
            
            # Explicitly close memory buffers to free up RAM
            buffer.close()
            image_bytes.close()
            
        instance.save()
        return f"Image {image_id} was successfully processed."
        
    except TemporaryAdImage.DoesNotExist:
        return f"Image {image_id} was not found."
