"""
AI-powered rewrite suggestions using Anthropic Claude API.

This module generates improved versions of resume content based on:
- Job description signals (what the job wants)
- Evidence matches (what's already in the resume)
- Original content (what to improve)
"""
import json
import os
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv

from app.models.content_unit import ContentUnit, ParsedResume
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


def _build_rewrite_prompt(
    content_unit: ContentUnit,
    jd_signals: JobDescriptionSignals,
    evidence_map: EvidenceMap,
    all_content_units: list[ContentUnit],
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

    prompt = f"""You are an expert resume writer helping optimize a resume for an Applicant Tracking System (ATS).

**CRITICAL CONSTRAINTS:**
1. NEVER add skills, tools, technologies, or metrics that are NOT already in the resume
2. NEVER change the meaning or make false claims
3. ONLY improve wording, clarity, and alignment with the job description
4. Keep the same length or slightly shorter (ATS-friendly)
5. Use action verbs and quantifiable results when possible
6. Make it more ATS-friendly (use standard terminology)

**JOB DESCRIPTION REQUIREMENTS:**
Key Skills: {', '.join(jd_skills)}
Key Responsibilities: {', '.join(jd_responsibilities[:5])}

**EVIDENCE IN THIS RESUME UNIT:**
{chr(10).join(relevant_evidence) if relevant_evidence else 'No direct evidence matches found for this unit.'}

**ORIGINAL TEXT TO IMPROVE:**
{content_unit.content}

**CONTENT UNIT TYPE:** {content_unit.type}

**TASK:**
Rewrite the above text to better align with the job description while:
- Preserving the original meaning and truthfulness
- Only using information already present in the resume
- Making it more ATS-friendly and impactful
- Using stronger action verbs and clearer language

**OUTPUT FORMAT (JSON):**
{{
  "suggested_text": "Your improved version here",
  "reasoning": "Brief explanation of improvements (2-3 sentences)",
  "jd_alignment": {{
    "skills_addressed": ["list of JD skills this addresses"],
    "responsibilities_addressed": ["list of JD responsibilities this addresses"]
  }},
  "preserves_meaning": true,
  "confidence": 0.0-1.0
}}

Return ONLY valid JSON, no additional text."""

    return prompt


def suggest_rewrite_for_unit(
    content_unit: ContentUnit,
    jd_signals: JobDescriptionSignals,
    evidence_map: EvidenceMap,
    all_content_units: list[ContentUnit],
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
        prompt = _build_rewrite_prompt(content_unit, jd_signals, evidence_map, all_content_units)

        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.3,  # Lower temperature for more consistent, factual outputs
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
        suggestion = RewriteSuggestion(
            content_unit_id=content_unit.id,
            original_text=content_unit.content,
            suggested_text=response_data.get("suggested_text", content_unit.content),
            confidence=response_data.get("confidence", 0.7),
            reasoning=response_data.get("reasoning", "Improved alignment with job description"),
            jd_alignment=response_data.get("jd_alignment", {}),
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
            type_priority.get(u.type.value, 99),  # Then by type priority
        ),
    )

    # Generate suggestions for prioritized units
    for unit in sorted_units[:max_suggestions]:
        # Skip very short content units
        if len(unit.content.strip()) < 10:
            continue

        suggestion = suggest_rewrite_for_unit(unit, jd_signals, evidence_map, resume.content_units)
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
    }

    return RewriteSuggestions(
        suggestions=suggestions,
        total_suggestions=len(suggestions),
        coverage_improvement=coverage_improvement,
        metadata=metadata,
    )
