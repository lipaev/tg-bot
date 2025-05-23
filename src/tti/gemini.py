from google import genai
import os
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

result = client.models.generate_images(
    model="models/gemini-2.0-flash-preview-image-generation",  #models/imagen-3.0-generate-002
    prompt="""INSERT_INPUT_HERE""",
    config=dict(
        number_of_images=1,
        output_mime_type="image/jpeg",
        person_generation="ALLOW_ADULT",
        aspect_ratio="1:1",
    ),
)

if len(result.generated_images) != 1:
    print("Number of images generated does not match the requested number.")

for generated_image in result.generated_images:
    image = Image.open(BytesIO(generated_image.image.image_bytes))
    image.show()