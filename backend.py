import os
import io
import json
import time
import hashlib
import base64
import logging
import re
import random
import numpy as np
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# ==================== CONFIGURATION ====================

# Brand Colors (Endo Health style)
BRAND_COLORS = {
    "pink": "#A32A53",
    "cream": "#F7EDF3",
    "white": "#FFFFFF",
    "lavender": "#B8A4E8"
}

# Image sizes
FINAL_WIDTH = 1200
FINAL_HEIGHT = 630
GENERATION_SIZE = 1024

# Output folder
OUTPUT_DIR = Path(__file__).parent / "endo_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# API Keys (from .env file)
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
TOGETHER_AI_API_KEY = os.getenv("TOGETHER_AI_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

# Check API keys
if not TOGETHER_AI_API_KEY:
    raise ValueError("⚠️ TOGETHER_AI_API_KEY not found in .env file")
if not NVIDIA_API_KEY:
    raise ValueError("⚠️ NVIDIA_API_KEY not found in .env file")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==================== STYLE CONTROL ====================

def build_minimal_prompt(analysis):
    """Build concise image generation prompt for women's health illustration"""
    topic = analysis.get("topic", "women wellness")
    elements = ", ".join(analysis.get("visual_elements", [])) or "soft healing elements, gentle botanical accents, flowing organic shapes"
    
    prompt = f"""
    professional editorial illustration for women's health magazine
    high quality digital art, soft watercolor style
    subject should occupy 60-70% of frame
    detailed scene with multiple elements, rich background, and layered composition
    soft pastel pink, lavender, cream tones, warm and inviting
    soft diffused natural lighting, calm and supportive atmosphere
    prominent central figure, supporting decorative elements
    calming, hopeful, trustworthy mood
    clean, polished finish suitable for medical publication

    BLOG POST TITLE: {topic}
    illustration elements: {elements}

    IMPORTANT: full, detailed scene with depth; avoid minimal or sparse composition
    """
    return prompt


def is_valid_hex(color):
    """Validate hex color format"""
    if not color or not isinstance(color, str):
        return False
    return bool(re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color.strip()))


def get_topic_color_mapping():
    """Map health topics to appropriate brand colors"""
    return {
        "endometriosis": [BRAND_COLORS["pink"], BRAND_COLORS["lavender"]],
        "pms": [BRAND_COLORS["cream"], BRAND_COLORS["lavender"]],
        "menopause": [BRAND_COLORS["lavender"], BRAND_COLORS["cream"]],
        "fertility": [BRAND_COLORS["pink"], BRAND_COLORS["cream"]],
        "nutrition": [BRAND_COLORS["cream"], BRAND_COLORS["lavender"]],
        "interview": [BRAND_COLORS["pink"], BRAND_COLORS["lavender"]],
        "wellness": [BRAND_COLORS["cream"], BRAND_COLORS["lavender"]],
        "general": [BRAND_COLORS["pink"], BRAND_COLORS["cream"]]
    }


def get_brand_color_for_topic(topic):
    """Get appropriate brand colors for a specific health topic"""
    topic_mapping = get_topic_color_mapping()
    return topic_mapping.get(topic.lower(), [BRAND_COLORS["pink"], BRAND_COLORS["cream"]])


def validate_and_enforce_brand_colors(colors):
    """Validate colors and ensure they are from the brand palette"""
    if not colors or not isinstance(colors, list):
        return [BRAND_COLORS["pink"], BRAND_COLORS["cream"]]
    
    # Filter to only brand colors
    brand_colors = [c.strip() for c in colors if is_valid_hex(c) and c.strip() in BRAND_COLORS.values()]
    
    # If no brand colors found, use defaults
    if not brand_colors:
        return [BRAND_COLORS["pink"], BRAND_COLORS["cream"]]
    
    # If only one brand color, add a complementary one
    if len(brand_colors) == 1:
        primary = brand_colors[0]
        if primary == BRAND_COLORS["pink"]:
            brand_colors.append(BRAND_COLORS["cream"])
        elif primary == BRAND_COLORS["lavender"]:
            brand_colors.append(BRAND_COLORS["cream"])
        else:
            brand_colors.append(BRAND_COLORS["pink"])
    
    return brand_colors[:2]


def get_topic_from_title(title):
    """
    Do title analysis
    Returns: topic name, suggested colors, visual elements
    """
    together_result = _analyze_with_together_ai(title)
    if together_result:
        together_result["colors"] = validate_and_enforce_brand_colors(together_result.get("colors", []))
        return together_result
    
    # Fallback to default values
    logger.warning("⚠️ API analysis failed, using default fallback")
    return {
        "topic": "wellness",
        "colors": [BRAND_COLORS["pink"], BRAND_COLORS["cream"]],
        "visual_elements": ["soft abstract shapes", "gentle waves", "healing light"]
    }


def _analyze_with_together_ai(title):
    """Analyze title using Together AI"""
    url = "https://api.together.xyz/v1/chat/completions"  # ✅ FIXED: No trailing spaces
    
    headers = {
        "Authorization": f"Bearer {TOGETHER_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Analyze this women's health blog title: "{title}"
    
    Return JSON with:
    - topic: one of [endometriosis, pms, menopause, fertility, nutrition, interview, wellness, general]
    - colors: 2 hex colors from this palette: {list(BRAND_COLORS.values())}
    - visual_elements: 3 simple visual ideas (e.g., "flowers", "calm waves", "healing light")
    
    Return ONLY valid JSON, no other text.
    """
    
    data = {
        "model": "meta-llama/Llama-3-8b-chat-hf",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        logger.info("🔍 Analyzing title with Together AI...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        assistant_message = response_data['choices'][0]['message']['content'].strip()
        
        if assistant_message:
            # Clean response and parse JSON
            text = assistant_message
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            if text:
                parsed = json.loads(text)
                
                if isinstance(parsed, dict):
                    # Validate colors
                    if "colors" in parsed:
                        parsed["colors"] = [c.strip() for c in parsed["colors"] if is_valid_hex(c)]
                        if not parsed["colors"]:
                            parsed["colors"] = [BRAND_COLORS["pink"], BRAND_COLORS["lavender"]]
                    
                    logger.info("✅ Together AI analysis successful")
                    return parsed
        
    except Exception as e:
        logger.debug(f"Together AI failed: {e}")
    
    return None


def generate_image(prompt, seed=None):
    """
    Generate image using NVIDIA Flux API
    Returns: image bytes
    """
    url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"  # ✅ FIXED: No trailing spaces
    
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use provided seed or generate random one
    if seed is None:
        seed = random.randint(1, 1000000)
    
    payload = {
        "prompt": prompt,
        "width": GENERATION_SIZE,
        "height": GENERATION_SIZE,
        "seed": seed,
        "steps": 4
    }
    
    logger.info(f"🎨 Sending prompt to NVIDIA Flux...")
    
    # Retry logic with exponential backoff
    for attempt in range(1, 4):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            
            logger.info(f"📡 NVIDIA API Response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate response structure
                if "artifacts" not in result or not result["artifacts"]:
                    logger.error("❌ No artifacts in NVIDIA response")
                    raise RuntimeError("Empty image response from NVIDIA")
                
                img_base64 = result["artifacts"][0]["base64"]
                img_bytes = base64.b64decode(img_base64)
                
                # Validate image is not empty/black
                test_img = Image.open(io.BytesIO(img_bytes))
                img_array = np.array(test_img)
                mean_brightness = np.mean(img_array[:, :, :3])
                
                logger.info(f"📊 Image brightness: {mean_brightness:.1f}/255")
                
                if mean_brightness < 50:
                    logger.warning(f"⚠️ Generated image too dark (brightness: {mean_brightness:.1f})")
                    if attempt < 3:
                        payload["seed"] = random.randint(1, 1000000)  # Try different seed
                        logger.info(f"🔄 Retrying with new seed: {payload['seed']}")
                        continue
                
                logger.info(f"✅ Image generated successfully")
                return img_bytes
                
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2))
                logger.warning(f"⏳ Rate limited, waiting {retry_after}s")
                time.sleep(retry_after)
                continue
            else:
                logger.error(f"❌ Attempt {attempt}: API error {response.status_code} - {response.text[:300]}")
        
        except Exception as e:
            logger.error(f"❌ Attempt {attempt}: {e}")
        
        if attempt < 3:
            wait_time = (2 ** attempt) + random.uniform(0.5, 1.5)
            logger.info(f"⏳ Waiting {wait_time:.1f}s before retry...")
            time.sleep(wait_time)
    
    raise RuntimeError("❌ Image generation failed after 3 attempts")


def create_fallback_gradient(width, height, base_color):
    """Create a soft gradient fallback when image generation fails"""
    gradient = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(gradient)
    
    # Create soft watercolor-like gradient
    for i in range(0, height, 15):
        ratio = i / height
        # Blend between base color and white
        r = int(base_color[0] * (1 - ratio * 0.5) + 255 * ratio * 0.5)
        g = int(base_color[1] * (1 - ratio * 0.5) + 255 * ratio * 0.5)
        b = int(base_color[2] * (1 - ratio * 0.5) + 255 * ratio * 0.5)
        draw.line([(0, i), (width, i)], fill=(r, g, b, 255), width=15)
    
    # Add subtle organic shapes
    for _ in range(5):
        x = random.randint(0, width)
        y = random.randint(0, height)
        radius = random.randint(50, 150)
        alpha = random.randint(30, 80)
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=(*base_color, alpha)
        )
    
    return gradient


def wrap_text(draw, text, font, max_width):
    """Break text into multiple lines if too long"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        
        if bbox[2] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    # Limit to 4 lines max
    if len(lines) > 4:
        lines = lines[:4]
        if not lines[-1].endswith("..."):
            lines[-1] = lines[-1][:-3] + "..."
    
    return lines


def get_font(size=72):
    """Load font with multiple fallbacks - ✅ FIXED: Larger default size"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "arial.ttf",
        "Arial.ttf",
        "Helvetica.ttf"
    ]
    
    for path in font_paths:
        try:
            font = ImageFont.truetype(path, size)
            logger.info(f"✅ Font loaded: {path}")
            return font
        except (IOError, OSError, FileNotFoundError):
            continue
    
    # Last resort - try default with size
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        # Older PIL versions don't support size parameter
        return ImageFont.load_default()


def create_banner(image_bytes, title, accent_color):
    """
    Create final banner with title on left, image on right
    Returns: PIL Image object
    """
    # Validate accent color
    if not is_valid_hex(accent_color):
        accent_color = BRAND_COLORS["pink"]
    
    # Convert hex to RGB tuple for PIL
    hex_color = accent_color.lstrip('#')
    rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Calculate sections
    left_width = int(FINAL_WIDTH * 0.40)
    right_width = FINAL_WIDTH - left_width
    
    # Load generated image
    try:
        ai_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        
        # 🔧 Check if image is mostly black (generation failed)
        ai_image_array = np.array(ai_image)
        mean_brightness = np.mean(ai_image_array[:, :, :3])
        
        logger.info(f"📊 Generated image brightness: {mean_brightness:.1f}/255")
        
        if mean_brightness < 50:
            logger.warning("⚠️ Generated image too dark, using fallback gradient")
            ai_image = create_fallback_gradient(right_width, FINAL_HEIGHT, rgb_color)
        else:
            ai_image = ImageOps.fit(ai_image, (right_width, FINAL_HEIGHT))
    
    except Exception as e:
        logger.error(f"❌ Failed to load generated image: {e}")
        ai_image = create_fallback_gradient(right_width, FINAL_HEIGHT, rgb_color)
    
    # Create left panel with color
    left_panel = Image.new("RGBA", (left_width, FINAL_HEIGHT), (*rgb_color, 255))
    
    # Combine left and right
    canvas = Image.new("RGBA", (FINAL_WIDTH, FINAL_HEIGHT), (255, 255, 255, 255))
    canvas.paste(left_panel, (0, 0))
    canvas.paste(ai_image, (left_width, 0))
    
    # Add title text
    draw = ImageDraw.Draw(canvas)
    
    # 🔧 FIXED: Increased font size from 49 to 72
    font = get_font(72)
    
    # Wrap title text
    margin = 40  # 🔧 Increased from 30 for better padding
    max_width = left_width - (margin * 2)
    lines = wrap_text(draw, title, font, max_width)
    
    # Calculate vertical center with proper line heights
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    
    line_spacing = 15  # Space between lines
    total_height = sum(line_heights) + (len(lines) - 1) * line_spacing
    y = (FINAL_HEIGHT - total_height) // 2
    
    # Draw each line with better spacing
    for i, line in enumerate(lines):
        draw.text((margin, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_heights[i] + line_spacing
    
    # Convert to RGB and return
    final_image = canvas.convert("RGB")
    return final_image


def save_image(image, title, index):
    """Save image to file with safe filename"""
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in title.lower())[:50]
    safe_name = safe_name.strip(" _-")
    filename = f"{index:02d}_{safe_name}.png"
    filepath = OUTPUT_DIR / filename
    
    image.save(filepath, format="PNG", optimize=True, quality=95)
    logger.info(f"💾 Saved: {filepath}")
    return filename


# ==================== MAIN GENERATION FUNCTION ====================

def generate_header(title, index):
    """Generate one complete header image"""
    start_time = time.time()
    
    result = {
        "index": index,
        "title": title,
        "status": "started",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Step 1: Analyze title with Together.ai
        logger.info(f"[{index:02d}] Analyzing: {title[:50]}...")
        analysis = get_topic_from_title(title)
        result["topic"] = analysis.get("topic", "general")
        
        # Step 2: Build image prompt
        prompt = build_prompt(analysis)
        logger.info(f"[{index:02d}] Prompt built ({len(prompt)} chars)")
        
        # Step 3: Generate image with NVIDIA Flux
        logger.info(f"[{index:02d}] Generating image...")
        seed = int(hashlib.sha1(title.encode()).hexdigest()[:8], 16) % 1000000
        image_bytes = generate_image(prompt, seed)
        
        # Step 4: Create banner with title
        logger.info(f"[{index:02d}] Creating banner...")
        colors = analysis.get("colors", [BRAND_COLORS["pink"]])
        accent_color = colors[0] if colors else BRAND_COLORS["pink"]
        banner = create_banner(image_bytes, title, accent_color)
        
        # Step 5: Save image
        filename = save_image(banner, title, index)
        result["filename"] = filename
        result["color"] = accent_color
        
        # Success!
        elapsed = time.time() - start_time
        result["status"] = "success"
        result["duration"] = round(elapsed, 2)
        logger.info(f"[{index:02d}] ✅ Saved: {filename} ({elapsed:.1f}s)")
        
    except Exception as e:
        elapsed = time.time() - start_time
        result["status"] = "failed"
        result["error"] = str(e)
        result["duration"] = round(elapsed, 2)
        logger.error(f"[{index:02d}] ❌ Failed: {e}")
    
    return result


def generate_batch(titles):
    """Generate headers for multiple titles"""
    logger.info(f"🚀 Starting generation for {len(titles)} titles")
    
    all_results = []
    
    for i, title in enumerate(titles, 1):
        result = generate_header(title, i)
        all_results.append(result)
    
    # Save metadata
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total": len(titles),
        "results": all_results
    }
    
    metadata_path = OUTPUT_DIR / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Summary
    success_count = sum(1 for r in all_results if r["status"] == "success")
    logger.info(f"✅ Complete: {success_count}/{len(titles)} images")
    
    return all_results


# ==================== TEST RUN ====================

if __name__ == "__main__":
    TEST_TITLES = [
        "Interview with Silke Neumann on Home Remedies for Endometriosis",
        "Insights from Fertility Specialist Silvia Hecher",
        "How Our Nervous System Affects Well-being",
        "Does Dienogest Increase Surgery Risk?",
        "Finding the Perfect Nutritionist Guide",
        "Managing PMS Symptoms Naturally",
        "Menopause Myths Debunked",
        "Endometriosis Pain Relief Strategies",
        "Nutrition Tips for Adenomyosis",
        "Building an SOS Plan for Flare-Ups"
    ]
    
    print("\n" + "="*60)
    print("🌸 ENDO HEALTH HEADER GENERATOR - TEST RUN")
    print("="*60)
    print(f"Output folder: {OUTPUT_DIR.absolute()}")
    print("="*60 + "\n")
    
    results = generate_batch(TEST_TITLES)
    
    print("\n" + "="*60)
    print("📊 GENERATION SUMMARY")
    print("="*60)
    for r in results:
        status = "✅" if r["status"] == "success" else "❌"
        duration = r.get("duration", 0)
        print(f"{status} {r['index']:02d}. {r['title'][:45]}... ({duration}s)")
    print("="*60)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\n🎉 Success: {success_count}/{len(results)} images")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}")











