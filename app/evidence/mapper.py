"""
Evidence mapper that matches JD signals to resume content units.

This module prevents hallucinations by only suggesting rewrites based on
existing evidence in the resume.
"""
import re
from typing import Optional

from app.models.content_unit import ContentUnit, ContentUnitType, ParsedResume
from app.models.evidence import (
    EvidenceMatch,
    EvidenceMap,
    KeywordMatch,
    MatchType,
    ResponsibilityMatch,
    SkillMatch,
    UnsupportedRequirement,
)
from app.models.jd_signals import HardSkill, JDKeyword, JobDescriptionSignals, Responsibility


def calculate_confidence_score(
    match_type: str, exact_match: bool, partial_match: bool, similarity_ratio: float = 0.0
) -> float:
    """
    Calculate confidence score for a match.

    Args:
        match_type: Type of match ("exact", "variation", "partial", "semantic")
        exact_match: Whether this is an exact string match
        partial_match: Whether this is a partial match
        similarity_ratio: Ratio of similarity (0.0-1.0) for fuzzy matches

    Returns:
        Confidence score between 0.0 and 1.0
    """
    if exact_match:
        return 1.0
    elif match_type == "variation" and partial_match:
        return 0.9
    elif match_type == "partial" and partial_match:
        return min(0.8, 0.5 + similarity_ratio * 0.3)
    elif match_type == "semantic" and similarity_ratio > 0.7:
        return 0.7
    elif match_type == "semantic" and similarity_ratio > 0.5:
        return 0.5
    elif partial_match:
        return 0.6
    else:
        return 0.0


def _normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, remove punctuation)."""
    text = text.lower()
    # Remove common punctuation but keep spaces
    text = re.sub(r"[^\w\s]", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple similarity ratio between two texts.

    Uses word overlap ratio as a simple similarity metric.
    For production, consider using more sophisticated methods like Levenshtein distance
    or semantic embeddings.
    """
    words1 = set(_normalize_text(text1).split())
    words2 = set(_normalize_text(text2).split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union) if union else 0.0


def _find_skill_in_content(skill: HardSkill, content: str) -> tuple[bool, bool, float, str]:
    """
    Find a skill in resume content.

    Returns:
        Tuple of (found, exact_match, similarity_ratio, match_reason)
    """
    content_lower = content.lower()
    skill_name_lower = skill.name.lower()

    # Check for exact match
    if skill_name_lower in content_lower:
        return True, True, 1.0, f"Exact match of skill '{skill.name}'"

    # Check variations
    for variation in skill.variations:
        if variation.lower() in content_lower:
            return True, False, 0.9, f"Match via variation '{variation}' for skill '{skill.name}'"

    # Check for partial match (skill name as word boundary)
    pattern = r"\b" + re.escape(skill_name_lower) + r"\b"
    if re.search(pattern, content_lower):
        return True, True, 1.0, f"Exact word match of skill '{skill.name}'"

    # Check for partial substring match
    if skill_name_lower in content_lower:
        similarity = _calculate_similarity(skill.name, content)
        return True, False, similarity, f"Partial match of skill '{skill.name}'"

    return False, False, 0.0, ""


def match_skills(
    jd_skills: list[HardSkill], resume: ParsedResume
) -> tuple[list[SkillMatch], list[UnsupportedRequirement]]:
    """
    Match JD hard skills to resume content units.

    Searches in SKILLS_LINE and EXPERIENCE_BULLET content units.

    Args:
        jd_skills: List of hard skills from JD
        resume: Parsed resume with content units

    Returns:
        Tuple of (skill_matches, unsupported_skills)
    """
    skill_matches: list[SkillMatch] = []
    unsupported_skills: list[UnsupportedRequirement] = []

    # Get relevant content units (skills section and experience bullets)
    skills_units = [u for u in resume.content_units if u.type == ContentUnitType.SKILLS_LINE]
    experience_units = [u for u in resume.content_units if u.type == ContentUnitType.EXPERIENCE_BULLET]

    all_relevant_units = skills_units + experience_units

    for skill in jd_skills:
        jd_item_id = f"skill_{skill.name.lower().replace(' ', '_')}_{id(skill)}"
        matches: list[EvidenceMatch] = []
        matched_units: list[dict] = []
        max_confidence = 0.0

        # Search in all relevant content units
        for unit in all_relevant_units:
            found, exact_match, similarity, reason = _find_skill_in_content(skill, unit.content)

            if found:
                confidence = calculate_confidence_score(
                    "variation" if not exact_match else "exact", exact_match, True, similarity
                )
                max_confidence = max(max_confidence, confidence)

                match = EvidenceMatch(
                    jd_item_id=jd_item_id,
                    resume_unit_id=unit.id,
                    confidence=confidence,
                    match_type=MatchType.SKILL,
                    match_reason=reason,
                    jd_item_data=skill.model_dump(),
                    resume_unit_content=unit.content,
                )
                matches.append(match)
                matched_units.append(unit.model_dump())

        if matches:
            skill_matches.append(
                SkillMatch(
                    jd_skill=skill.model_dump(),
                    resume_bullets=matched_units,
                    confidence=max_confidence,
                    match_details=matches,
                )
            )
        else:
            unsupported_skills.append(
                UnsupportedRequirement(
                    type="skill",
                    name=skill.name,
                    jd_item_data=skill.model_dump(),
                    reason=f"No evidence found for skill '{skill.name}' in resume",
                )
            )

    return skill_matches, unsupported_skills


def _find_responsibility_in_content(resp: Responsibility, content: str) -> tuple[bool, float, str]:
    """
    Find a responsibility in resume content.

    Returns:
        Tuple of (found, confidence, match_reason)
    """
    content_lower = content.lower()
    verb_lower = resp.verb.lower()
    object_lower = resp.object.lower()
    full_text_lower = resp.full_text.lower()

    # Check for full text match (highest confidence)
    if full_text_lower in content_lower:
        return True, 0.9, f"Full responsibility text match: '{resp.full_text}'"

    # Check for both verb and object
    verb_found = verb_lower in content_lower or any(
        word in content_lower for word in verb_lower.split() if len(word) > 3
    )
    object_found = object_lower in content_lower

    if verb_found and object_found:
        similarity = _calculate_similarity(resp.full_text, content)
        confidence = 0.7 + (similarity * 0.2)  # 0.7-0.9 range
        return True, confidence, f"Both verb '{resp.verb}' and object '{resp.object}' found"

    # Check for object only (often more specific)
    if object_found:
        similarity = _calculate_similarity(resp.object, content)
        confidence = 0.6 + (similarity * 0.2)  # 0.6-0.8 range
        return True, confidence, f"Object '{resp.object}' found in content"

    # Check for verb only (less specific)
    if verb_found:
        similarity = _calculate_similarity(resp.verb, content)
        confidence = 0.5 + (similarity * 0.1)  # 0.5-0.6 range
        return True, confidence, f"Verb '{resp.verb}' found in content"

    # Check for semantic similarity
    similarity = _calculate_similarity(resp.full_text, content)
    if similarity > 0.5:
        return True, similarity * 0.7, f"Semantic similarity ({similarity:.2f}) with '{resp.full_text}'"

    return False, 0.0, ""


def match_responsibilities(
    jd_responsibilities: list[Responsibility], resume: ParsedResume
) -> tuple[list[ResponsibilityMatch], list[UnsupportedRequirement]]:
    """
    Match JD responsibilities to resume experience bullets.

    Args:
        jd_responsibilities: List of responsibilities from JD
        resume: Parsed resume with content units

    Returns:
        Tuple of (responsibility_matches, unsupported_responsibilities)
    """
    responsibility_matches: list[ResponsibilityMatch] = []
    unsupported_responsibilities: list[UnsupportedRequirement] = []

    # Only search in experience bullets
    experience_units = [u for u in resume.content_units if u.type == ContentUnitType.EXPERIENCE_BULLET]

    for resp in jd_responsibilities:
        jd_item_id = f"resp_{resp.verb.lower().replace(' ', '_')}_{id(resp)}"
        matches: list[EvidenceMatch] = []
        matched_units: list[dict] = []
        max_confidence = 0.0

        # Search in experience bullets
        for unit in experience_units:
            found, confidence, reason = _find_responsibility_in_content(resp, unit.content)

            if found and confidence > 0.0:
                max_confidence = max(max_confidence, confidence)

                match = EvidenceMatch(
                    jd_item_id=jd_item_id,
                    resume_unit_id=unit.id,
                    confidence=confidence,
                    match_type=MatchType.RESPONSIBILITY,
                    match_reason=reason,
                    jd_item_data=resp.model_dump(),
                    resume_unit_content=unit.content,
                )
                matches.append(match)
                matched_units.append(unit.model_dump())

        if matches:
            responsibility_matches.append(
                ResponsibilityMatch(
                    jd_responsibility=resp.model_dump(),
                    resume_bullets=matched_units,
                    confidence=max_confidence,
                    match_details=matches,
                )
            )
        else:
            unsupported_responsibilities.append(
                UnsupportedRequirement(
                    type="responsibility",
                    name=resp.full_text,
                    jd_item_data=resp.model_dump(),
                    reason=f"No evidence found for responsibility '{resp.full_text}' in resume",
                )
            )

    return responsibility_matches, unsupported_responsibilities


def _find_keyword_in_content(keyword: JDKeyword, content: str) -> tuple[bool, float, str]:
    """
    Find a keyword in resume content.

    Returns:
        Tuple of (found, confidence, match_reason)
    """
    content_lower = content.lower()
    keyword_lower = keyword.keyword.lower()

    # Exact match
    if keyword_lower in content_lower:
        return True, 1.0, f"Exact keyword match: '{keyword.keyword}'"

    # Word boundary match
    pattern = r"\b" + re.escape(keyword_lower) + r"\b"
    if re.search(pattern, content_lower):
        return True, 1.0, f"Exact word match of keyword '{keyword.keyword}'"

    # Partial match
    if keyword_lower in content_lower:
        similarity = _calculate_similarity(keyword.keyword, content)
        confidence = 0.7 + (similarity * 0.2)  # 0.7-0.9 range
        return True, confidence, f"Partial match of keyword '{keyword.keyword}'"

    # Check for individual words in multi-word keywords
    keyword_words = keyword_lower.split()
    if len(keyword_words) > 1:
        matched_words = sum(1 for word in keyword_words if word in content_lower and len(word) > 3)
        if matched_words >= len(keyword_words) * 0.6:  # At least 60% of words
            similarity = _calculate_similarity(keyword.keyword, content)
            return True, 0.6 + (similarity * 0.2), f"Partial word match of keyword '{keyword.keyword}'"

    return False, 0.0, ""


def match_keywords(
    jd_keywords: list[JDKeyword], resume: ParsedResume
) -> tuple[list[KeywordMatch], list[UnsupportedRequirement]]:
    """
    Find JD keywords in resume content units.

    Searches in all content unit types.

    Args:
        jd_keywords: List of keywords from JD
        resume: Parsed resume with content units

    Returns:
        Tuple of (keyword_matches, unsupported_keywords)
    """
    keyword_matches: list[KeywordMatch] = []
    unsupported_keywords: list[UnsupportedRequirement] = []

    # Search in all content units
    all_units = resume.content_units

    for keyword in jd_keywords:
        jd_item_id = f"keyword_{keyword.keyword.lower().replace(' ', '_')}_{id(keyword)}"
        matches: list[EvidenceMatch] = []
        matched_units: list[dict] = []
        max_confidence = 0.0

        # Search in all content units
        for unit in all_units:
            found, confidence, reason = _find_keyword_in_content(keyword, unit.content)

            if found and confidence > 0.0:
                max_confidence = max(max_confidence, confidence)

                match = EvidenceMatch(
                    jd_item_id=jd_item_id,
                    resume_unit_id=unit.id,
                    confidence=confidence,
                    match_type=MatchType.KEYWORD,
                    match_reason=reason,
                    jd_item_data=keyword.model_dump(),
                    resume_unit_content=unit.content,
                )
                matches.append(match)
                matched_units.append(unit.model_dump())

        if matches:
            keyword_matches.append(
                KeywordMatch(
                    jd_keyword=keyword.model_dump(),
                    resume_units=matched_units,
                    confidence=max_confidence,
                    match_details=matches,
                )
            )
        else:
            unsupported_keywords.append(
                UnsupportedRequirement(
                    type="keyword",
                    name=keyword.keyword,
                    jd_item_data=keyword.model_dump(),
                    reason=f"No evidence found for keyword '{keyword.keyword}' in resume",
                )
            )

    return keyword_matches, unsupported_keywords


def map_evidence(jd_signals: JobDescriptionSignals, resume: ParsedResume) -> EvidenceMap:
    """
    Map JD signals to resume content units to find evidence.

    This is the main orchestrator function that:
    1. Matches skills
    2. Matches responsibilities
    3. Matches keywords
    4. Calculates coverage score
    5. Identifies unsupported requirements

    Args:
        jd_signals: Extracted JD signals from Step 3
        resume: Parsed resume content from Step 1

    Returns:
        EvidenceMap with all matches and coverage metrics
    """
    # Match skills
    skill_matches, unsupported_skills = match_skills(jd_signals.hard_skills, resume)

    # Match responsibilities
    responsibility_matches, unsupported_responsibilities = match_responsibilities(
        jd_signals.responsibilities, resume
    )

    # Match keywords
    keyword_matches, unsupported_keywords = match_keywords(jd_signals.keywords, resume)

    # Combine all unsupported requirements
    unsupported_requirements = unsupported_skills + unsupported_responsibilities + unsupported_keywords

    # Calculate coverage score
    total_requirements = (
        len(jd_signals.hard_skills) + len(jd_signals.responsibilities) + len(jd_signals.keywords)
    )
    matched_requirements = (
        len(skill_matches) + len(responsibility_matches) + len(keyword_matches)
    )

    coverage_score = matched_requirements / total_requirements if total_requirements > 0 else 0.0

    # Build metadata
    metadata = {
        "total_jd_requirements": total_requirements,
        "matched_requirements": matched_requirements,
        "unsupported_requirements": len(unsupported_requirements),
        "skill_matches_count": len(skill_matches),
        "responsibility_matches_count": len(responsibility_matches),
        "keyword_matches_count": len(keyword_matches),
    }

    return EvidenceMap(
        skill_matches=skill_matches,
        responsibility_matches=responsibility_matches,
        keyword_matches=keyword_matches,
        unsupported_requirements=unsupported_requirements,
        coverage_score=coverage_score,
        metadata=metadata,
    )
