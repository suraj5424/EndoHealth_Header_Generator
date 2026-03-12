#!/usr/bin/env python3
"""
Endo Health Header Generator - Streamlit Cloud Optimized
Simple web interface using Streamlit (Clean UX - No Ellipsis)
"""

import os
import streamlit as st
from pathlib import Path
import zipfile
import time
import tempfile
from datetime import datetime

# Import backend functions
from backend import generate_header, generate_batch, OUTPUT_DIR, BRAND_COLORS

# ==================== PAGE SETUP ====================

st.set_page_config(
    page_title="Endo Health Header Generator",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for larger images and better styling
st.markdown("""
<style>
/* Larger image preview */
.stImage img {
    max-height: 650px !important;
    width: 100% !important;
    object-fit: contain;
    border-radius: 12px;
}

/* Result cards */
.result-card {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 20px;
    margin: 12px 0;
    border: 1px solid #e9ecef;
}

/* Large title preview inside expander */
.title-preview {
    font-size: 26px;
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: 10px;
}

/* Expander titles */
.streamlit-expanderHeader {
    font-size: 18px !important;
    font-weight: 600 !important;
}

/* Text */
.full-title {
    white-space: normal !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
    font-size: 20px !important;
}

/* Sidebar cards */
.sidebar-info {
    background: #f0f2f6;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
}

/* Title input textarea */
textarea {
    font-size: 16px !important;
}
</style>
""", unsafe_allow_html=True)


# Page title
st.title("🌸 Endo Health Header Generator")
st.markdown("*AI-powered blog header images for women's health content*")

# ==================== SIDEBAR (Information Only) ====================

with st.sidebar:
    st.markdown("### 🎨 Brand Identity")
    st.markdown("Consistent visual style for Endo Health blog headers")
    
    # Brand Colors with visual swatches
    st.markdown("#### Primary Colors")
    color_cols = st.columns(2)
    color_items = list(BRAND_COLORS.items())
    for i, (name, color) in enumerate(color_items):
        with color_cols[i % 2]:
            st.markdown(
                f"<div style='background:{color}; padding:12px; border-radius:8px; "
                f"text-align:center; color:white; margin:8px 0; "
                f"text-shadow:0 1px 2px rgba(0,0,0,0.3); font-weight:bold;'>"
                f"{color}<br/><small>{name}</small></div>",
                unsafe_allow_html=True
            )
    
    st.markdown("---")
    
    # Image Specifications
    st.markdown("### 📐 Image Specifications")
    st.markdown("""
    <div class="sidebar-info">
    <table style="width:100%; font-size:0.9em;">
        <tr><td><b>Dimensions</b></td><td>1200 × 630 px</td></tr>
        <tr><td><b>Format</b></td><td>PNG (optimized)</td></tr>
        <tr><td><b>Text Area</b></td><td>Left 40%</td></tr>
        <tr><td><b>Image Area</b></td><td>Right 60%</td></tr>
        <tr><td><b>Style</b></td><td>Soft watercolor</td></tr>
    </table>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # How It Works
    st.markdown("### 🔍 How It Works")
    st.markdown("""
    <div class="sidebar-info">
    <ol style="padding-left:20px; margin:0;">
        <li>AI analyzes your blog title</li>
        <li>Extracts topic & visual theme</li>
        <li>Generates matching watercolor image</li>
        <li>Applies brand colors & typography</li>
        <li>Exports ready-to-use header</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # API Status (without showing keys)
    st.markdown("### 🔑 API Status")
    
    together_configured = bool(os.getenv("TOGETHER_AI_API_KEY"))
    nvidia_configured = bool(os.getenv("NVIDIA_API_KEY"))
    
    if together_configured:
        st.success("✅ Together.ai (LLM)")
    else:
        st.error("❌ Together.ai (LLM)")
        st.caption("Set `TOGETHER_AI_API_KEY` in Secrets")
    
    if nvidia_configured:
        st.success("✅ NVIDIA Flux (Images)")
    else:
        st.error("❌ NVIDIA Flux (Images)")
        st.caption("Set `NVIDIA_API_KEY` in Secrets")
    
    st.markdown("---")
    
    # Quick Tips
    st.markdown("### 💡 Tips")
    st.markdown("""
    <div class="sidebar-info">
    <ul style="padding-left:20px; margin:0; font-size:0.85em;">
        <li>Keep titles under 60 characters for best results</li>
        <li>One title per line</li>
        <li>Batch up to 20 titles at once</li>
        <li>Images saved to temporary storage</li>
        <li>Download all as ZIP when done</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Output Folder Info
    st.markdown("### 📁 Storage")
    st.caption("Using temporary storage for Streamlit Cloud")
    
    # Count existing files
    if OUTPUT_DIR.exists():
        png_count = len(list(OUTPUT_DIR.glob("*.png")))
        st.info(f"📊 {png_count} images in folder")
    
    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🗑️ Clear Output Folder", width='stretch'):
        if OUTPUT_DIR.exists():
            for f in OUTPUT_DIR.glob("*.png"):
                f.unlink()
            for f in OUTPUT_DIR.glob("*.json"):
                f.unlink()
            for f in OUTPUT_DIR.glob("*.zip"):
                f.unlink()
            st.success("✅ Output folder cleared!")
            st.rerun()
    
    if st.button("🔄 Refresh Page", width='stretch'):
        st.rerun()
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style="text-align:center; color:#888; font-size:0.8em; padding:20px 0;">
    <b>Endo Health GmbH</b><br/>
    AI Solutions Engineer Challenge 2026<br/>
    <small>Powered by Together.ai + NVIDIA</small>
    </div>
    """, unsafe_allow_html=True)

# ==================== MAIN AREA ====================

# Status banner at top
if not together_configured or not nvidia_configured:
    st.warning("""
    ⚠️ **API Keys Not Configured**
    
    Please set the following environment variables in your Streamlit Cloud Secrets:
    - `TOGETHER_AI_API_KEY` - For title analysis
    - `NVIDIA_API_KEY` - For image generation
    """)

st.markdown("### 📝 Enter Blog Titles")
st.caption("Paste your blog post titles below, one per line")

# Default titles
default_titles = """Interview with Silke Neumann on Home Remedies for Endometriosis
Insights from Fertility Specialist Silvia Hecher
How Our Nervous System Affects Well-being
Does Dienogest Increase Surgery Risk?
Finding the Perfect Nutritionist Guide
Managing PMS Symptoms Naturally
Menopause Myths Debunked
Endometriosis Pain Relief Strategies
Nutrition Tips for Adenomyosis
Building an SOS Plan for Flare-Ups"""

titles_input = st.text_area(
    "Blog Titles",
    value=default_titles,
    height=400,
    placeholder="Enter your blog titles here, one per line...",
    label_visibility="collapsed"
)

# Title count preview
title_count = len([t for t in titles_input.split("\n") if t.strip()])
st.caption(f"📊 {title_count} titles detected")

# Generate button
st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

generate_btn = st.button(
    "🎨 Generate All Headers",
    type="primary",
    width='stretch',
    disabled=not (together_configured and nvidia_configured) or title_count == 0
)

# Character limit warning
long_titles = [t for t in titles_input.split("\n") if len(t.strip()) > 80 and t.strip()]
if long_titles:
    st.warning(f"⚠️ {len(long_titles)} title(s) exceed 80 characters and may wrap in the image")

st.markdown("### 📊 Generation Results")
st.caption("Generated images will appear here")

# Initialize session state for results
if "generation_results" not in st.session_state:
    st.session_state.generation_results = []
if "generation_complete" not in st.session_state:
    st.session_state.generation_complete = False

if generate_btn and together_configured and nvidia_configured:
    # Parse titles
    titles = [t.strip() for t in titles_input.split("\n") if t.strip()]
    
    if len(titles) == 0:
        st.warning("⚠️ Please enter at least one title")
    else:
        # Clear previous results
        st.session_state.generation_results = []
        st.session_state.generation_complete = False
        
        # Progress container
        progress_container = st.container()
        with progress_container:
            st.info(f"🚀 Starting generation of **{len(titles)}** headers...")
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Results container for images
        results_container = st.container()
        
        # Generate all with real-time updates
        all_results = []
        
        for i, title in enumerate(titles, 1):
            # Update progress
            progress_bar.progress(i / len(titles))
            status_text.text(f"⏳ Processing {i}/{len(titles)}: {title}")
            
            # Generate single header
            result = generate_header(title, i)
            all_results.append(result)
            
            # Display result immediately with larger image - NO ELLIPSIS
            with results_container:
                expander_label = f"{'✅' if result['status']=='success' else '❌'} #{i:02d} - {title}"
                
                with st.expander(expander_label, expanded=True):
                    if result["status"] == "success":
                        # Display larger image
                        image_path = OUTPUT_DIR / result["filename"]
                        if image_path.exists():
                            st.image(
                                image_path,
                                caption=f"🎨 {result.get('topic', 'General')} | "
                                        f"Color: {result.get('color', 'N/A')} | "
                                        f"⏱️ {result.get('duration', 0)}s",
                                width='stretch'
                            )
                        
                        # Metadata row
                        meta_col1, meta_col2, meta_col3 = st.columns(3)
                        with meta_col1:
                            st.markdown(f"**File:** `{result['filename']}`")
                        with meta_col2:
                            st.markdown(f"**Topic:** {result.get('topic', 'N/A')}")
                        with meta_col3:
                            st.markdown(f"**Time:** {result.get('duration', 0)}s")
                    else:
                        st.error(f"❌ Generation failed")
                        with st.expander("🔍 Error Details"):
                            st.code(result.get('error', 'Unknown error'))
        
        # Complete
        progress_bar.progress(1.0)
        status_text.empty()
        st.session_state.generation_results = all_results
        st.session_state.generation_complete = True
        
        # Final summary
        st.markdown("---")
        success_count = sum(1 for r in all_results if r["status"] == "success")
        
        if success_count == len(titles):
            st.success(f"🎉 **All {len(titles)} headers generated successfully!**")
        elif success_count > 0:
            st.warning(f"⚠️ **{success_count}/{len(titles)}** headers generated ({len(titles)-success_count} failed)")
        else:
            st.error(f"❌ **All generations failed.** Check API keys and logs.")
        
        # Download section
        png_files = list(OUTPUT_DIR.glob("*.png"))
        if png_files:
            st.markdown("### 📦 Download")
            
            # Create ZIP
            zip_path = OUTPUT_DIR / "headers.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for f in png_files:
                    zipf.write(f, arcname=f.name)
            
            # Download button
            with open(zip_path, "rb") as f:
                st.download_button(
                    label=f"📥 Download All {len(png_files)} Images (ZIP)",
                    data=f.read(),
                    file_name=f"endo_headers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    width='stretch'
                )
            
            # Individual download info
            st.caption(f"💾 Also saved to: `{OUTPUT_DIR.absolute()}`")

# Show previous results if available
elif st.session_state.generation_results and not generate_btn:
    st.info("ℹ️ Previous generation results shown below")
    
    for i, result in enumerate(st.session_state.generation_results, 1):
        expander_label = f"{'✅' if result['status']=='success' else '❌'} #{i:02d} - {result['title']}"
        
        with st.expander(expander_label, expanded=False):
            if result["status"] == "success":
                image_path = OUTPUT_DIR / result.get("filename", "")
                if image_path.exists():
                    st.image(
                        image_path,
                        caption=f"🎨 {result.get('topic', 'General')} | "
                                f"Color: {result.get('color', 'N/A')}",
                        width='stretch'
                    )
            else:
                st.error(f"❌ Generation failed: {result.get('error', 'Unknown')}")

# ==================== INFO SECTION ====================

st.markdown("---")

st.markdown("### 📚 Documentation")

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:
    with st.container():
        st.markdown("#### 🔍 How It Works")
        st.markdown("""
        1. **Title Analysis** - Together.ai extracts topic and theme
        2. **Color Selection** - AI suggests brand-appropriate colors
        3. **Image Generation** - NVIDIA Flux creates watercolor artwork
        4. **Composition** - Title overlay applied with proper spacing
        5. **Export** - PNG saved with metadata tracking
        """)

with info_col2:
    with st.container():
        st.markdown("#### 🎨 Brand Guidelines")
        st.markdown("""
        - **Style:** Soft, warm, professional
        - **Palette:** Pink, lavender, cream tones
        - **Mood:** Calming, supportive, trustworthy
        - **Format:** 1200×630px (Open Graph standard)
        - **Text:** White on colored background (left 40%)
        """)

with info_col3:
    with st.container():
        st.markdown("#### 📁 File Output")
        st.markdown("""
        - **Images:** `endo_output/XX_title.png`
        - **Meta** `endo_output/metadata.json`
        - **Archive:** `endo_output/headers.zip`
        - **Logs:** Console + timestamped entries
        """)

# ==================== FOOTER ====================

st.markdown("---")

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("**🏢 Endo Health GmbH**")
    st.caption("Women's Health Solutions")

with footer_col2:
    st.markdown("**🤖 AI Technology**")
    st.caption("Together.ai + NVIDIA Flux")

with footer_col3:
    st.markdown("**📅 2026**")
    st.caption("AI Solutions Engineer Challenge")

st.markdown("""
<div style="text-align:center; color:#aaa; padding:30px 0; border-top:1px solid #eee; margin-top:30px;">
<small>© 2026 Endo Health GmbH. All rights reserved.</small>
</div>
""", unsafe_allow_html=True)


