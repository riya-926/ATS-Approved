"""
AI-powered rewrite suggestions using Anthropic Claude API.

This module generates improved versions of resume content based on:
- Job description signals (what the job wants)
- Evidence matches (what's already in the resume)
- Original content (what to improve)
"""
import json
import os
from collections import defaultdict
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv

from app.models.content_unit import ContentUnit, ContentUnitType, ParsedResume
from app.models.evidence import EvidenceMap
from app.models.jd_signals import JobDescriptionSignals
from app.models.rewrite import RewriteSuggestion, RewriteSuggestions

# Load environment variables
load_dotenv()

# Initialize Anthropic client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY not found in environment variables. "
        "Please create a .env file with your API key."
    )

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def _analyze_bullet_point_consistency(resume: ParsedResume) -> dict:
    """
    Analyze bullet point counts per experience/project section.
    
    Returns:
        dict with:
        - 'target_bullets': Target number of bullets per section (2 or 3)
        - 'experience_bullet_counts': Dict mapping section to bullet count
        - 'project_bullet_counts': Dict mapping section to bullet count
        - 'is_consistent': Whether all sections have same count
    """
    # Group bullets by section (using section_index or paragraph_index)
    experience_bullets = [u for u in resume.content_units if u.type == ContentUnitType.EXPERIENCE_BULLET]
    project_bullets = [u for u in resume.content_units if u.type == ContentUnitType.PROJECT_DESCRIPTION]
    
    # Count bullets per section
    exp_sections = defaultdict(int)
    proj_sections = defaultdict(int)
    
    for bullet in experience_bullets:
        section_key = bullet.section_index if bullet.section_index is not None else 0
        exp_sections[section_key] += 1
    
    for bullet in project_bullets:
        section_key = bullet.section_index if bullet.section_index is not None else 0
        proj_sections[section_key] += 1
    
    # Determine target bullet count
    all_exp_counts = list(exp_sections.values()) if exp_sections else []
    all_proj_counts = list(proj_sections.values()) if proj_sections else []
    all_counts = all_exp_counts + all_proj_counts
    
    if not all_counts:
        return {
            'target_bullets': 3,
            'experience_bullet_counts': dict(exp_sections),
            'project_bullet_counts': dict(proj_sections),
            'is_consistent': True
        }
    
    # If all sections have same count, use that
    if len(set(all_counts)) == 1:
        target = all_counts[0]
    # If mostly 3 bullets, target 3
    elif all_counts.count(3) >= len(all_counts) * 0.5:
        target = 3
    # Otherwise target 2-3 (prefer 3 but allow 2)
    else:
        target = 3  # Default to 3, but allow flexibility
    
    is_consistent = len(set(all_counts)) == 1
    
    return {
        'target_bullets': target,
        'experience_bullet_counts': dict(exp_sections),
        'project_bullet_counts': dict(proj_sections),
        'is_consistent': is_consistent
    }


def _estimate_resume_length(resume: ParsedResume) -> dict:
    """
    Estimate resume length in pages.
    
    Returns:
        dict with:
        - 'estimated_pages': Estimated page count
        - 'total_chars': Total character count
        - 'total_words': Total word count
        - 'needs_compression': Whether needs to be compressed to 1 page
    """
    total_chars = sum(len(unit.content) for unit in resume.content_units)
    total_words = sum(len(unit.content.split()) for unit in resume.content_units)
    
    # Rough estimate: ~500 words per page, ~2500 chars per page
    estimated_pages = max(total_words / 500, total_chars / 2500)
    
    return {
        'estimated_pages': estimated_pages,
        'total_chars': total_chars,
        'total_words': total_words,
        'needs_compression': estimated_pages > 1.0
    }


def _build_rewrite_prompt(
    content_unit: ContentUnit,
    jd_signals: JobDescriptionSignals,
    evidence_map: EvidenceMap,
    all_content_units: list[ContentUnit],
    bullet_analysis: dict,
    length_analysis: dict,
) -> str:
    """
    Build a detailed prompt for Claude to generate rewrite suggestions.

    Args:
        content_unit: The content unit to rewrite
        jd_signals: Job description signals
        evidence_map: Evidence mapping between JD and resume
        all_content_units: All content units for context

    Returns:
        Formatted prompt string
    """
    # Find relevant evidence for this content unit
    relevant_evidence = []
    for skill_match in evidence_map.skill_matches:
        for match_detail in skill_match.match_details:
            if match_detail.resume_unit_id == content_unit.id:
                relevant_evidence.append(
                    f"Skill Match: {skill_match.jd_skill['name']} (confidence: {skill_match.confidence:.2f})"
                )

    for resp_match in evidence_map.responsibility_matches:
        for match_detail in resp_match.match_details:
            if match_detail.resume_unit_id == content_unit.id:
                relevant_evidence.append(
                    f"Responsibility Match: {resp_match.jd_responsibility['full_text']} (confidence: {resp_match.confidence:.2f})"
                )

    # Build JD requirements summary
    jd_skills = [skill.name for skill in jd_signals.hard_skills[:10]]  # Top 10
    jd_responsibilities = [resp.full_text for resp in jd_signals.responsibilities[:10]]  # Top 10

    # Determine tense from original text (for consistency)
    original_text_lower = content_unit.content.lower()
    is_past_tense = any(
        word in original_text_lower
        for word in ["developed", "designed", "implemented", "created", "built", "managed", "led", "improved", "optimized", "delivered", "achieved", "increased", "reduced", "maintained"]
    )
    is_present_tense = any(
        word in original_text_lower
        for word in ["develop", "design", "implement", "create", "build", "manage", "lead", "improve", "optimize", "deliver", "achieve", "increase", "reduce", "maintain"]
    )
    
    tense_instruction = ""
    if is_past_tense:
        tense_instruction = "CRITICAL: Maintain PAST TENSE throughout (e.g., 'developed', 'designed', 'implemented'). Do NOT mix tenses."
    elif is_present_tense:
        tense_instruction = "CRITICAL: Maintain PRESENT TENSE throughout (e.g., 'develop', 'design', 'implement'). Do NOT mix tenses."
    else:
        tense_instruction = "CRITICAL: Maintain the same verb tense as the original text. Do NOT change tense."
    
    # Bullet point consistency instructions
    bullet_instruction = ""
    if content_unit.type in [ContentUnitType.EXPERIENCE_BULLET, ContentUnitType.PROJECT_DESCRIPTION]:
        target_bullets = bullet_analysis.get('target_bullets', 3)
        is_consistent = bullet_analysis.get('is_consistent', True)
        if not is_consistent:
            bullet_instruction = f"CRITICAL: Ensure this section has exactly {target_bullets} bullet points. All experience/project sections must have the same number of bullets ({target_bullets}) for consistency."
        else:
            bullet_instruction = f"Maintain {target_bullets} bullet points per section for consistency."
    
    # Page limit instructions
    page_instruction = ""
    if length_analysis.get('needs_compression', False):
        estimated_pages = length_analysis.get('estimated_pages', 1.0)
        page_instruction = f"CRITICAL: Resume is currently {estimated_pages:.1f} pages. MUST compress to exactly 1 page. Make text more concise, remove redundant information, combine similar points. Target: ~500 words total, ~2500 characters total."
    else:
        page_instruction = "Keep resume to 1 page maximum. If approaching limit, prioritize conciseness."

    prompt = f"""You are an expert ATS resume optimizer. Your goal is to achieve 80%+ ATS compatibility score while making ONLY meaningful, impactful improvements.

**CRITICAL CONSTRAINTS (NON-NEGOTIABLE):**
1. NEVER add skills, tools, technologies, metrics, or achievements NOT already in the resume
2. NEVER change the meaning, make false claims, or exaggerate accomplishments
3. NEVER change verb tense - {tense_instruction}
4. REMOVE all fluff words: "very", "really", "quite", "rather", "somewhat", "fairly", "pretty", "extremely", "incredibly", "absolutely", "totally", "completely", "basically", "essentially", "generally", "usually", "typically", "often", "sometimes"
5. Use standard ATS-friendly terminology (avoid jargon, abbreviations without context, or overly creative phrasing)
6. {page_instruction}
7. {bullet_instruction}
8. Keep length similar or slightly shorter (ATS parsers prefer concise, scannable text)
9. Only make changes if they meaningfully improve ATS parsing or JD alignment - don't change for the sake of changing

**ATS OPTIMIZATION REQUIREMENTS (Target: 80%+ score):**
- Use standard industry terminology that ATS systems recognize
- Include relevant keywords from the job description naturally
- Use clear, direct language (avoid passive voice when possible)
- Quantify achievements with numbers/metrics when available
- Use strong action verbs at the start of bullet points
- Avoid special characters that break ATS parsing (em dashes, fancy quotes, etc.)

**JOB DESCRIPTION REQUIREMENTS (MUST FOLLOW):**
- Key Skills to align with: {', '.join(jd_skills) if jd_skills else 'None specified'}
- Key Responsibilities to address: {', '.join(jd_responsibilities[:5]) if jd_responsibilities else 'None specified'}
- CRITICAL: Use JD keywords and terminology naturally. Prioritize JD alignment when rewording.

**EVIDENCE IN THIS RESUME UNIT:**
{chr(10).join(relevant_evidence) if relevant_evidence else 'No direct evidence matches found for this unit. Focus on ATS optimization and clarity improvements only.'}

**ORIGINAL TEXT TO IMPROVE:**
{content_unit.content}

**CONTENT UNIT TYPE:** {content_unit.type}

**TASK:**
Rewrite the above text to achieve 80%+ ATS compatibility while:
- Preserving EXACT meaning and truthfulness (no exaggeration)
- Maintaining the SAME verb tense as original
- Removing ALL fluff words and filler language
- Using standard ATS-recognized terminology
- Aligning with JD keywords naturally (only if already present in resume)
- Making ONLY meaningful improvements (if original is already strong, make minimal changes)
- Keeping structure and formatting intact

**IMPORTANT:**
- If the original text is already well-written and ATS-friendly, make MINIMAL changes
- Only suggest changes that meaningfully improve ATS parsing or JD alignment
- Prioritize clarity, conciseness, and ATS keyword optimization
- Do NOT add unnecessary words or phrases

**OUTPUT FORMAT (JSON):**
{{
  "suggested_text": "Your improved version here (maintain tense, remove fluff, optimize for ATS)",
  "reasoning": "Brief explanation of improvements (2-3 sentences). Explain how this improves ATS score and JD alignment.",
  "jd_alignment": {{
    "skills_addressed": ["list of JD skills this addresses"],
    "responsibilities_addressed": ["list of JD responsibilities this addresses"],
    "ats_keywords_added": ["list of ATS-friendly keywords naturally incorporated"]
  }},
  "preserves_meaning": true,
  "confidence": 0.0-1.0,
  "estimated_ats_score_improvement": "Low/Medium/High"
}}

Return ONLY valid JSON, no additional text."""

    return prompt


def suggest_rewrite_for_unit(
    content_unit: ContentUnit,
    jd_signals: JobDescriptionSignals,
    evidence_map: EvidenceMap,
    all_content_units: list[ContentUnit],
    bullet_analysis: dict,
    length_analysis: dict,
) -> Optional[RewriteSuggestion]:
    """
    Generate a rewrite suggestion for a single content unit.

    Args:
        content_unit: The content unit to rewrite
        jd_signals: Job description signals
        evidence_map: Evidence mapping
        all_content_units: All content units for context

    Returns:
        RewriteSuggestion or None if generation fails
    """
    try:
        # Build prompt
        prompt = _build_rewrite_prompt(content_unit, jd_signals, evidence_map, all_content_units, bullet_analysis, length_analysis)

        # Call Claude API
        # Note: Model names may vary based on your API access level
        # Common formats: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-haiku-20240307
        # If you get 404 errors, check Anthropic console for available models
        message = client.messages.create(
            model="claude-3-haiku-20240307",  # Using Haiku (fastest, most available)
            max_tokens=1024,
            temperature=0.2,  # Lower temperature for more consistent, factual outputs (reduced from 0.3 for better accuracy)
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        # Parse response
        response_text = message.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks if present)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        response_data = json.loads(response_text)

        # Build RewriteSuggestion
        jd_alignment = response_data.get("jd_alignment", {})
        # Add estimated ATS score improvement if provided
        if "estimated_ats_score_improvement" in response_data:
            jd_alignment["estimated_ats_score_improvement"] = response_data.get("estimated_ats_score_improvement")
        
        suggestion = RewriteSuggestion(
            content_unit_id=content_unit.id,
            original_text=content_unit.content,
            suggested_text=response_data.get("suggested_text", content_unit.content),
            confidence=response_data.get("confidence", 0.7),
            reasoning=response_data.get("reasoning", "Improved alignment with job description and ATS optimization"),
            jd_alignment=jd_alignment,
            preserves_meaning=response_data.get("preserves_meaning", True),
            risk_score=0.0,  # Will be calculated by validators later
        )

        return suggestion

    except Exception as e:
        print(f"Error generating rewrite for unit {content_unit.id}: {str(e)}")
        return None


def suggest_rewrites(
    jd_signals: JobDescriptionSignals,
    evidence_map: EvidenceMap,
    resume: ParsedResume,
    max_suggestions: int = 10,
) -> RewriteSuggestions:
    """
    Generate rewrite suggestions for resume content units.

    This is the main function that orchestrates rewrite generation.

    Args:
        jd_signals: Job description signals
        evidence_map: Evidence mapping between JD and resume
        resume: Parsed resume with content units
        max_suggestions: Maximum number of suggestions to generate

    Returns:
        RewriteSuggestions with all generated suggestions
    """
    suggestions: list[RewriteSuggestion] = []

    # Analyze bullet point consistency
    bullet_analysis = _analyze_bullet_point_consistency(resume)
    
    # Analyze resume length
    length_analysis = _estimate_resume_length(resume)

    # Prioritize content units with evidence matches
    units_with_evidence = set()
    for skill_match in evidence_map.skill_matches:
        for match_detail in skill_match.match_details:
            units_with_evidence.add(match_detail.resume_unit_id)
    for resp_match in evidence_map.responsibility_matches:
        for match_detail in resp_match.match_details:
            units_with_evidence.add(match_detail.resume_unit_id)

    # Sort content units: those with evidence first, then by type priority
    type_priority = {
        "experience_bullet": 1,
        "summary": 2,
        "skills_line": 3,
        "project_description": 4,
        "education_description": 5,
    }

    sorted_units = sorted(
        resume.content_units,
        key=lambda u: (
            u.id not in units_with_evidence,  # Units with evidence first
            type_priority.get(u.type, 99),  # Then by type priority (u.type is already a string due to use_enum_values=True)
        ),
    )

    # Generate suggestions for prioritized units
    for unit in sorted_units[:max_suggestions]:
        # Skip very short content units
        if len(unit.content.strip()) < 10:
            continue

        suggestion = suggest_rewrite_for_unit(unit, jd_signals, evidence_map, resume.content_units, bullet_analysis, length_analysis)
        if suggestion:
            suggestions.append(suggestion)

    # Calculate coverage improvement estimate
    total_units = len(resume.content_units)
    suggested_units = len(suggestions)
    coverage_improvement = (suggested_units / total_units) * evidence_map.coverage_score if total_units > 0 else 0.0

    metadata = {
        "total_content_units": total_units,
        "units_with_evidence": len(units_with_evidence),
        "suggestions_generated": len(suggestions),
        "coverage_score_before": evidence_map.coverage_score,
        "bullet_analysis": bullet_analysis,
        "length_analysis": length_analysis,
    }

    return RewriteSuggestions(
        suggestions=suggestions,
        total_suggestions=len(suggestions),
        coverage_improvement=coverage_improvement,
        metadata=metadata,
    )
