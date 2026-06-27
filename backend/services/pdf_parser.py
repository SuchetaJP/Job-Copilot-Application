"""
services/pdf_parser.py - Parse resume PDFs into structured text

Uses pypdf to extract text and attempts basic structure detection
for sections like Education, Experience, Skills, etc.
"""

import io
from typing import Dict, Any
from pypdf import PdfReader


def parse_resume_pdf(pdf_content: bytes) -> Dict[str, Any]:
    """
    Parse a resume PDF into text and structured sections.
    
    Args:
        pdf_content: Raw PDF file bytes
    
    Returns:
        Dict containing:
        - text: Full extracted text
        - sections: Dict of detected sections (best effort)
        - page_count: Number of pages
    
    WHY NOT USE OCR?
    Most resumes are text-based PDFs where text is directly extractable.
    OCR (Tesseract) would be needed for scanned documents but adds
    complexity and dependencies. This handles 95% of cases.
    """
    # Create a file-like object from bytes
    pdf_file = io.BytesIO(pdf_content)
    reader = PdfReader(pdf_file)
    
    # Extract all text
    all_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            all_text.append(text)
    
    full_text = "\n\n".join(all_text)
    
    # Attempt to detect sections
    sections = detect_resume_sections(full_text)
    
    return {
        "text": full_text,
        "sections": sections,
        "page_count": len(reader.pages)
    }


def detect_resume_sections(text: str) -> Dict[str, str]:
    """
    Attempt to split resume into common sections.
    
    This is heuristic-based and won't be perfect, but helps
    agents understand resume structure.
    
    Common section headers we look for:
    - Experience / Work Experience / Employment
    - Education / Academic
    - Skills / Technical Skills / Core Competencies
    - Projects / Portfolio
    - Certifications / Licenses
    - Summary / Profile / Objective
    """
    # Define section header patterns (case-insensitive)
    section_patterns = {
        "summary": ["summary", "profile", "objective", "about"],
        "experience": ["experience", "employment", "work history", "professional experience"],
        "education": ["education", "academic", "qualifications"],
        "skills": ["skills", "technical skills", "core competencies", "technologies"],
        "projects": ["projects", "portfolio", "personal projects"],
        "certifications": ["certifications", "licenses", "certificates"],
    }
    
    lines = text.split("\n")
    sections = {}
    current_section = "header"  # Before any section header
    current_content = []
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Check if this line is a section header
        found_section = None
        for section_name, patterns in section_patterns.items():
            if any(pattern in line_lower for pattern in patterns):
                # Simple heuristic: section headers are usually short
                if len(line_lower) < 40:
                    found_section = section_name
                    break
        
        if found_section:
            # Save previous section
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = found_section
            current_content = []
        else:
            current_content.append(line)
    
    # Save last section
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()
    
    return sections
