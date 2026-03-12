#!/usr/bin/env python3
"""
Endo Health Header Generator - Backend (Updated)
Uses Together.ai for LLM analysis + NVIDIA Flux for image generation
"""

import os
import io
import json
import time
import hashlib
import base64
import logging
import re
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
from dotenv import load_dotenv
import random


# Load environment variables
load_dotenv()

# ==================== CONFIGURATION ====================

# Brand Colors (Endo Health style) - FIXED: single #
BRAND_COLORS = {
    "pink": "#A32A53",
    "cream": "#F7EDF3",
    "white": "#FFFFFF",
    "lavender": "#B8A4E8"  # Added missing color
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
if not CEREBRAS_API_KEY:
    raise ValueError("⚠️ CEREBRAS_API_KEY not found in .env file")
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


# ==================== HELPER FUNCTIONS ====================


# ==================== STYLE CONTROL ====================

GLOBAL_STYLE = """
high quality editorial illustration for a modern women's health magazine

art style:
soft watercolor painting
delicate brush strokes
subtle paper texture
minimalist medical editorial art
modern digital health aesthetic

composition:
subject placed on the RIGHT side
large negative space on the LEFT
clean wide banner layout

color palette:
soft pastel pink
lavender
cream tones

lighting:
soft diffused lighting
calm warm atmosphere
"""

NEGATIVE_PROMPT = """
text, watermark, logo, typography,
low quality, blurry, distorted anatomy,
clipart, stock icon style, oversaturated colors
"""



def build_prompt(analysis):
    topic = analysis.get("topic", "women wellness")
    elements = ", ".join(analysis.get("visual_elements", []))

    prompt = f"""
    {GLOBAL_STYLE}

    topic focus: {topic}

    illustration elements:
    {elements}

    subject theme:
    women's health and wellness

    visual goal:
    calming, supportive, professional healthcare feeling

    no text in image
    """

    return prompt

def is_valid_hex(color):
    """Validate hex color format"""
    return bool(re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color))


def get_topic_color_mapping():
    """Map health topics to appropriate brand colors for better visual consistency"""
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
    if not colors:
        return [BRAND_COLORS["pink"], BRAND_COLORS["cream"]]
    
    # Filter to only brand colors
    brand_colors = [c for c in colors if c in BRAND_COLORS.values()]
    
    # If no brand colors found, use defaults
    if not brand_colors:
        return [BRAND_COLORS["pink"], BRAND_COLORS["cream"]]
    
    # If only one brand color, add a complementary one
    if len(brand_colors) == 1:
        primary = brand_colors[0]
        # Add a complementary color based on the primary
        if primary == BRAND_COLORS["pink"]:
            brand_colors.append(BRAND_COLORS["cream"])
        elif primary == BRAND_COLORS["lavender"]:
            brand_colors.append(BRAND_COLORS["cream"])
        else:
            brand_colors.append(BRAND_COLORS["pink"])
    
    return brand_colors[:2]  # Return maximum 2 colors



def get_topic_from_title(title):
    """
    Use Cerebras API as main service, with Together AI as backup
    Returns: topic name, suggested colors, visual elements
    """
    # Try Cerebras API first
    cerebras_result = _analyze_with_cerebras(title)
    if cerebras_result:
        # Validate and enforce brand colors
        cerebras_result["colors"] = validate_and_enforce_brand_colors(cerebras_result.get("colors", []))
        return cerebras_result
    
    # Fall back to Together AI if Cerebras fails
    logger.warning("Cerebras API failed, falling back to Together AI")
    together_result = _analyze_with_together_ai(title)
    if together_result:
        # Validate and enforce brand colors
        together_result["colors"] = validate_and_enforce_brand_colors(together_result.get("colors", []))
        return together_result
    
    # Final fallback to default values
    logger.warning("Both APIs failed, using default fallback")
    return {
        "topic": "general",
        "colors": [BRAND_COLORS["pink"], BRAND_COLORS["cream"]],
        "visual_elements": ["soft shapes", "gentle colors", "wellness icons"]
    }


def _analyze_with_cerebras(title):
    """Analyze title using Cerebras API"""
    url = "https://api.cerebras.ai/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CEREBRAS_API_KEY}"
    }
    
    prompt = f"""
    Analyze this women's health blog title: "{title}"
    
    Return JSON with:
    - topic: one of [endometriosis, pms, menopause, fertility, nutrition, interview, wellness, general]
    - colors: 2 hex colors from your brand palette: {list(BRAND_COLORS.values())}
    - visual_elements: 3 simple visual ideas (e.g., "flowers", "calm waves", "healing light")
    
    Return ONLY valid JSON, no other text.
    """
    
    data = {
        "stream": False,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_completion_tokens": -1,
        "seed": 0,
        "top_p": 1
    }
    
    # Try different models as shown in the example
    models = [
        "gpt-oss-120b",
        "llama3.1-8b", 
        "zai-gtm-4.7",
        "qwen-3-235b-a22b-instruct-2507"
    ]
    
    for model in models:
        try:
            response = requests.post(url, headers=headers, json={**data, "model": model}, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                assistant_message = response_data["choices"][0]["message"]["content"].strip()
                
                # Clean response and parse JSON
                text = assistant_message
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                if text:
                    parsed = json.loads(text)
                    
                    # Validate required fields
                    if isinstance(parsed, dict):
                        # Validate colors
                        if "colors" in parsed:
                            parsed["colors"] = [c for c in parsed["colors"] if is_valid_hex(c)]
                            if not parsed["colors"]:
                                parsed["colors"] = [BRAND_COLORS["pink"], BRAND_COLORS["lavender"]]
                        
                        logger.info(f"✅ Cerebras API successful with model: {model}")
                        return parsed
                
        except Exception as e:
            logger.debug(f"Cerebras model {model} failed: {e}")
            continue
    
    return None


def _analyze_with_together_ai(title):
    """Analyze title using Together AI as backup"""
    url = "https://api.together.xyz/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {TOGETHER_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    Analyze this women's health blog title: "{title}"
    
    Return JSON with:
    - topic: one of [endometriosis, pms, menopause, fertility, nutrition, interview, wellness, general]
    - colors: 2 hex colors from your brand palette: {list(BRAND_COLORS.values())}
    - visual_elements: 3 simple visual ideas (e.g., "flowers", "calm waves", "healing light")
    
    Return ONLY valid JSON, no other text.
    """
    
    data = {
        "model": "ServiceNow-AI/Apriel-1.5-15b-Thinker",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
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
                        parsed["colors"] = [c for c in parsed["colors"] if is_valid_hex(c)]
                        if not parsed["colors"]:
                            parsed["colors"] = [BRAND_COLORS["pink"], BRAND_COLORS["lavender"]]
                    
                    logger.info("✅ Together AI backup successful")
                    return parsed
        
    except Exception as e:
        logger.debug(f"Together AI failed: {e}")
    
    return None


def generate_image(prompt, seed=None):
    """
    Generate image using NVIDIA Flux API (exact format as provided)
    Returns: image bytes
    """
    # FIXED: Removed trailing spaces from URL
    url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"
    
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt,
        "width": GENERATION_SIZE,
        "height": GENERATION_SIZE,
        "seed": seed if seed else 0,
        "steps": 4
    }
    
    # Retry logic with exponential backoff
    for attempt in range(1, 4):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                img_base64 = result["artifacts"][0]["base64"]
                img_bytes = base64.b64decode(img_base64)
                logger.info(f"✅ Image generated successfully")
                return img_bytes
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2))
                logger.warning(f"Rate limited, waiting {retry_after}s")
                time.sleep(retry_after)
                continue
            else:
                logger.warning(f"Attempt {attempt}: API error {response.status_code} - {response.text[:200]}")
        
        except Exception as e:
            logger.warning(f"Attempt {attempt}: {e}")
        
        if attempt < 3:
            time.sleep((2 ** attempt) + random.uniform(0.5, 1.5))
    
    raise RuntimeError("❌ Image generation failed after 3 attempts")


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


def get_font(size=100):
    """Load font with multiple fallbacks"""
    font_paths = [
        "arial.ttf",
        "Helvetica.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
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
    ai_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    ai_image = ImageOps.fit(ai_image, (right_width, FINAL_HEIGHT))
    
    # Create left panel with color
    left_panel = Image.new("RGBA", (left_width, FINAL_HEIGHT), (*rgb_color, 255))
    
    # Combine left and right
    canvas = Image.new("RGBA", (FINAL_WIDTH, FINAL_HEIGHT), (255, 255, 255, 255))
    canvas.paste(left_panel, (0, 0))
    canvas.paste(ai_image, (left_width, 0))
    
    # Add title text
    draw = ImageDraw.Draw(canvas)
    font = get_font(32)
    
    # Wrap title text
    margin = 30
    max_width = left_width - (margin * 2)
    lines = wrap_text(draw, title, font, max_width)
    
    # Calculate vertical center
    total_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)
    y = (FINAL_HEIGHT - total_height) // 2
    
    # Draw each line
    for line in lines:
        draw.text((margin, y), line, font=font, fill=(255, 255, 255, 255))
        bbox = draw.textbbox((0, 0), line, font=font)
        y += bbox[3] + 10
    
    # Convert to RGB and save
    final_image = canvas.convert("RGB")
    return final_image


def save_image(image, title, index):
    """Save image to file with safe filename"""
    safe_name = "".join(c if c.isalnum() else "_" for c in title.lower())[:50]
    filename = f"{index:02d}_{safe_name}.png"
    filepath = OUTPUT_DIR / filename
    
    image.save(filepath, format="PNG", optimize=True)
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
        logger.info(f"[{index:02d}] Analyzing: {title[:40]}...")
        analysis = get_topic_from_title(title)
        result["topic"] = analysis.get("topic", "general")
        
        # Step 2: Build image prompt
        colors = ", ".join(analysis.get("colors", []))
        elements = ", ".join(analysis.get("visual_elements", []))
        
        prompt = build_prompt(analysis)
        
        # Step 3: Generate image with NVIDIA Flux
        logger.info(f"[{index:02d}] Generating image...")
        seed = int(hashlib.sha1(title.encode()).hexdigest()[:8], 16)
        image_bytes = generate_image(prompt, seed)
        
        # Step 4: Create banner with title
        logger.info(f"[{index:02d}] Creating banner...")
        accent_color = analysis.get("colors", [BRAND_COLORS["pink"]])[0]
        banner = create_banner(image_bytes, title, accent_color)
        
        # Step 5: Save image
        filename = save_image(banner, title, index)
        result["filename"] = filename
        result["color"] = accent_color
        
        # Success!
        elapsed = time.time() - start_time
        result["status"] = "success"
        result["duration"] = round(elapsed, 2)
        logger.info(f"[{index:02d}] ✅ Saved: {filename}")
        
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
    
    results = generate_batch(TEST_TITLES)
    
    print("\n" + "="*50)
    print("📊 GENERATION SUMMARY")
    print("="*50)
    for r in results:
        status = "✅" if r["status"] == "success" else "❌"
        print(f"{status} {r['index']}. {r['title'][:40]}...")
    print("="*50)

    print(f"Output folder: {OUTPUT_DIR}")

