# Endo Health Header Generator

A beautiful, AI-powered web application for generating consistent blog header images for women's health content.

## 🌸 What It Does

This tool helps content creators in the women's health space generate professional, on-brand header images automatically. Just paste your blog titles, and the system will:

- Analyze each title to understand the health topic
- Generate a custom watercolor-style illustration
- Apply your brand colors and typography
- Create perfectly sized headers ready for social media

## 🎨 Brand Identity

The generator follows Endo Health's visual guidelines:

- **Style**: Soft watercolor paintings with gentle brush strokes
- **Colors**: Pink (#A32A53), Lavender (#B8A4E8), Cream (#F7EDF3), White (#FFFFFF)
- **Layout**: Text on left (40%), image on right (60%)
- **Format**: 1200×630px (perfect for Open Graph/social sharing)

## 🔄 Workflow

The system follows a streamlined three-stage process:

1. **Input Processing** - Users paste blog titles into the web interface
2. **AI Analysis & Generation** - The backend analyzes topics and creates custom images
3. **Brand Application** - Final headers are assembled with consistent styling

## 🏗️ Architecture

### Frontend Layer
- Streamlit web interface for user interaction
- Real-time progress tracking and result display
- Batch processing capabilities
- Download functionality for individual or grouped images

### Backend Processing
- Title analysis using Together.ai for topic detection
- Image generation via NVIDIA Flux with watercolor style
- Brand compliance enforcement with predefined color palettes
- File management and metadata tracking

### AI Integration
- Dual API approach with fallback mechanisms
- Smart topic categorization for health content
- Automatic color selection based on content themes
- Consistent visual style generation

## 💡 How It Works

The magic happens in three steps:

1. **Title Analysis** - Together.ai analyzes your blog title to identify the health topic and suggest appropriate visual elements
2. **Image Generation** - NVIDIA Flux creates a custom watercolor illustration based on the analysis
3. **Brand Application** - The system applies your brand colors, typography, and layout to create the final header

## 📋 Features

- **Batch Processing**: Generate up to 20 headers at once
- **Smart Topic Detection**: Automatically identifies health topics (endometriosis, PMS, menopause, etc.)
- **Brand Consistency**: Ensures all headers follow your visual guidelines
- **Download Options**: Get individual images or a complete ZIP file
- **Real-time Preview**: See results as they're generated
- **Error Handling**: Clear feedback if something goes wrong

## 🎯 Use Cases

Perfect for:
- Health bloggers and content creators
- Women's health websites and magazines
- Medical professionals sharing educational content
- Health brands maintaining consistent social media presence

## 📁 Project Structure

The application is organized into clear layers:

**Interface Layer**: Streamlit web application providing user interaction
**Processing Layer**: Backend logic handling AI integration and image creation
**Storage Layer**: File management for generated images and metadata
**Configuration Layer**: Environment variables and dependency management

## 🔧 System Components

### AI Integration Architecture
- **Topic Analysis Engine**: Intelligent title parsing and health topic identification
- **Image Generation Pipeline**: Watercolor-style illustration creation with style consistency
- **Brand Compliance System**: Automated color and layout standardization
- **Error Recovery Mechanism**: Fallback strategies for API reliability

### Processing Flow
1. User input validation and preprocessing
2. Topic detection and visual element suggestion
3. Custom image generation with appropriate style
4. Brand application and final composition
5. Quality assurance and file output

## 🎯 Optimization Strategies

### Content Preparation
- Craft clear, descriptive titles that accurately reflect your content
- Use specific health terminology for better topic detection
- Maintain consistent title formatting for uniform results

### Performance Considerations
- Process similar topics together for visual consistency
- Monitor API usage and rate limits during batch operations
- Ensure stable internet connection for reliable AI service access

### Quality Assurance
- Review generated images for brand compliance
- Check file sizes for optimal web performance
- Validate social media preview appearance
