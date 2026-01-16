"""
Job Description Signal Extractor.

Extracts structured signals from job descriptions:
- Hard skills (tools, technologies)
- Responsibilities (verb + object patterns)
- Keywords/phrases
- Seniority cues

Uses deterministic, pattern-based extraction with normalization and deduplication.
"""
import re
from typing import Optional

from app.models.jd_signals import (
    HardSkill,
    JDKeyword,
    JobDescriptionSignals,
    Responsibility,
    ResponsibilityType,
    SeniorityCue,
    SkillCategory,
)

# Common skill synonyms and normalizations
SKILL_SYNONYMS = {
    "structured query language": "SQL",
    "sql": "SQL",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "python": "Python",
    "java": "Java",
    "c++": "C++",
    "c#": "C#",
    "react": "React",
    "angular": "Angular",
    "vue": "Vue.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "aws": "AWS",
    "amazon web services": "AWS",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "docker": "Docker",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "mysql": "MySQL",
    "redis": "Redis",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "jenkins": "Jenkins",
    "ci/cd": "CI/CD",
    "continuous integration": "CI/CD",
    "terraform": "Terraform",
    "kubernetes": "Kubernetes",
}

# Common programming languages
PROGRAMMING_LANGUAGES = {
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "go",
    "rust",
    "ruby",
    "php",
    "swift",
    "kotlin",
    "scala",
    "r",
    "matlab",
    "sql",
    "html",
    "css",
    "shell",
    "bash",
    "powershell",
}

# Common frameworks
FRAMEWORKS = {
    "react",
    "angular",
    "vue",
    "django",
    "flask",
    "fastapi",
    "express",
    "spring",
    "rails",
    "laravel",
    "asp.net",
    "next.js",
    "nuxt",
    "svelte",
}

# Common databases
DATABASES = {
    "postgresql",
    "postgres",
    "mysql",
    "mongodb",
    "redis",
    "cassandra",
    "elasticsearch",
    "dynamodb",
    "oracle",
    "sql server",
    "sqlite",
}

# Common tools/platforms
TOOLS_PLATFORMS = {
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "jenkins",
    "git",
    "github",
    "gitlab",
    "terraform",
    "ansible",
    "chef",
    "puppet",
    "splunk",
    "datadog",
    "grafana",
    "prometheus",
}

# Common action verbs for responsibilities
RESPONSIBILITY_VERBS = {
    "develop",
    "design",
    "implement",
    "build",
    "create",
    "maintain",
    "optimize",
    "debug",
    "test",
    "deploy",
    "manage",
    "lead",
    "architect",
    "collaborate",
    "communicate",
    "review",
    "refactor",
    "scale",
    "improve",
    "enhance",
    "analyze",
    "evaluate",
    "troubleshoot",
    "integrate",
    "configure",
    "automate",
    "monitor",
    "secure",
    "migrate",
    "document",
}


def extract_jd_signals(jd_text: str) -> JobDescriptionSignals:
    """
    Extract structured signals from a job description.

    Args:
        jd_text: Raw job description text

    Returns:
        JobDescriptionSignals with extracted signals
    """
    # Normalize text
    text_lower = jd_text.lower()
    text_lines = jd_text.split("\n")

    # Extract signals
    hard_skills = _extract_hard_skills(text_lower, jd_text)
    responsibilities = _extract_responsibilities(text_lower, jd_text)
    keywords = _extract_keywords(text_lower, jd_text)
    seniority_cues = _extract_seniority_cues(text_lower, jd_text)

    # Deduplicate and normalize
    hard_skills = _deduplicate_skills(hard_skills)
    keywords = _deduplicate_keywords(keywords)

    metadata = {
        "total_length": len(jd_text),
        "line_count": len(text_lines),
        "skills_count": len(hard_skills),
        "responsibilities_count": len(responsibilities),
    }

    return JobDescriptionSignals(
        hard_skills=hard_skills,
        responsibilities=responsibilities,
        keywords=keywords,
        seniority_cues=seniority_cues,
        raw_text=jd_text,
        metadata=metadata,
    )


def _extract_hard_skills(text_lower: str, original_text: str) -> list[HardSkill]:
    """Extract hard skills from job description."""
    skills = []
    skill_map: dict[str, HardSkill] = {}

    # Pattern: Look for common skill mentions
    all_skills = (
        list(PROGRAMMING_LANGUAGES)
        + list(FRAMEWORKS)
        + list(DATABASES)
        + list(TOOLS_PLATFORMS)
        + list(SKILL_SYNONYMS.keys())
    )

    for skill_lower in all_skills:
        # Create pattern that matches word boundaries
        pattern = r"\b" + re.escape(skill_lower) + r"\b"
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)

        if matches:
            # Normalize skill name
            normalized = SKILL_SYNONYMS.get(skill_lower, skill_lower.title())

            # Determine category
            category = _categorize_skill(skill_lower, normalized)

            # Count mentions
            mentions = len(list(matches))

            # Store in map (normalize key)
            if normalized not in skill_map:
                skill_map[normalized] = HardSkill(
                    name=normalized,
                    category=category,
                    variations=[skill_lower],
                    confidence=1.0 if mentions > 0 else 0.5,
                    mentions=mentions,
                )
            else:
                # Update existing skill
                existing = skill_map[normalized]
                existing.mentions += mentions
                if skill_lower not in existing.variations:
                    existing.variations.append(skill_lower)

    # Also look for common skill indicators
    # Pattern: "experience with X", "proficient in X", "knowledge of X"
    skill_patterns = [
        r"experience with\s+([A-Za-z][A-Za-z0-9\s]+?)(?:[,\.;]|\s+and)",
        r"proficient in\s+([A-Za-z][A-Za-z0-9\s]+?)(?:[,\.;]|\s+and)",
        r"knowledge of\s+([A-Za-z][A-Za-z0-9\s]+?)(?:[,\.;]|\s+and)",
        r"familiar with\s+([A-Za-z][A-Za-z0-9\s]+?)(?:[,\.;]|\s+and)",
    ]

    for pattern in skill_patterns:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            skill_text = match.group(1).strip()
            # Simple extraction - could be enhanced with NLP
            # For now, check if it matches known skills
            for known_skill in all_skills:
                if known_skill in skill_text.lower():
                    normalized = SKILL_SYNONYMS.get(known_skill, known_skill.title())
                    category = _categorize_skill(known_skill, normalized)

                    if normalized not in skill_map:
                        skill_map[normalized] = HardSkill(
                            name=normalized,
                            category=category,
                            variations=[skill_text],
                            confidence=0.8,
                            mentions=1,
                        )

    return list(skill_map.values())


def _categorize_skill(skill_lower: str, normalized: str) -> SkillCategory:
    """Categorize a skill based on its type."""
    if skill_lower in PROGRAMMING_LANGUAGES:
        return SkillCategory.PROGRAMMING_LANGUAGE
    elif skill_lower in FRAMEWORKS:
        return SkillCategory.FRAMEWORK
    elif skill_lower in DATABASES:
        return SkillCategory.DATABASE
    elif skill_lower in TOOLS_PLATFORMS:
        return SkillCategory.TOOL
    else:
        # Default categorization based on common patterns
        if "cloud" in skill_lower or skill_lower in ["aws", "azure", "gcp"]:
            return SkillCategory.PLATFORM
        elif "cert" in skill_lower or "certification" in skill_lower:
            return SkillCategory.CERTIFICATION
        else:
            return SkillCategory.TOOL


def _extract_responsibilities(text_lower: str, original_text: str) -> list[Responsibility]:
    """Extract responsibilities from job description."""
    responsibilities = []

    # Pattern: Verb + object (e.g., "develop REST APIs", "design microservices")
    # Look for common verb patterns
    verb_pattern = r"\b(" + "|".join(RESPONSIBILITY_VERBS) + r")\s+([^\.\n]+?)(?:[\.\n]|and|or|,)"

    matches = re.finditer(verb_pattern, text_lower, re.IGNORECASE)
    for match in matches:
        verb = match.group(1).lower()
        obj_text = match.group(2).strip()

        # Clean up object text
        obj_text = re.sub(r"^(a|an|the)\s+", "", obj_text, flags=re.IGNORECASE)
        obj_text = obj_text.strip()

        if len(obj_text) > 3 and len(obj_text) < 100:  # Reasonable length
            # Determine responsibility type
            resp_type = _categorize_responsibility(verb)

            # Get original case from original text
            full_text = original_text[match.start() : match.end()].strip()

            responsibilities.append(
                Responsibility(
                    verb=verb,
                    object=obj_text,
                    full_text=full_text,
                    type=resp_type,
                    confidence=0.9,
                )
            )

    return responsibilities[:20]  # Limit to top 20


def _categorize_responsibility(verb: str) -> ResponsibilityType:
    """Categorize a responsibility based on the verb."""
    verb = verb.lower()
    if verb in ["develop", "implement", "build", "create", "code", "program"]:
        return ResponsibilityType.DEVELOPMENT
    elif verb in ["design", "architect", "plan"]:
        return ResponsibilityType.DESIGN
    elif verb in ["test", "debug", "troubleshoot", "verify"]:
        return ResponsibilityType.TESTING
    elif verb in ["deploy", "configure", "automate", "monitor"]:
        return ResponsibilityType.DEVOPS
    elif verb in ["lead", "manage", "oversee", "direct"]:
        return ResponsibilityType.LEADERSHIP
    elif verb in ["collaborate", "communicate", "coordinate"]:
        return ResponsibilityType.COLLABORATION
    elif verb in ["analyze", "evaluate", "assess"]:
        return ResponsibilityType.ANALYSIS
    else:
        return ResponsibilityType.DEVELOPMENT


def _extract_keywords(text_lower: str, original_text: str) -> list[JDKeyword]:
    """Extract important keywords and phrases."""
    keywords = []
    keyword_map: dict[str, JDKeyword] = {}

    # Common important keywords/phrases
    important_patterns = [
        r"\bmicroservices\b",
        r"\bapi\b",
        r"\brest\b",
        r"\bgraphql\b",
        r"\bscalable\b",
        r"\bdistributed\b",
        r"\breal-time\b",
        r"\bcloud-native\b",
        r"\bdevops\b",
        r"\bci/cd\b",
        r"\bagile\b",
        r"\bscrum\b",
        r"\btdd\b",
        r"\btest-driven\b",
        r"\bclean code\b",
        r"\bdesign patterns\b",
        r"\bsystem design\b",
        r"\bdata structures\b",
        r"\balgorithms\b",
        r"\bmachine learning\b",
        r"\bai\b",
        r"\bdeep learning\b",
    ]

    for pattern in important_patterns:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            keyword = match.group(0).lower()
            if keyword not in keyword_map:
                keyword_map[keyword] = JDKeyword(
                    keyword=keyword,
                    category="technology",
                    importance=0.8,
                    mentions=1,
                )
            else:
                keyword_map[keyword].mentions += 1

    return list(keyword_map.values())


def _extract_seniority_cues(text_lower: str, original_text: str) -> list[SeniorityCue]:
    """Extract seniority level indicators."""
    cues = []

    # Pattern: Years of experience
    years_pattern = r"(\d+)\+?\s*years?\s*(?:of\s*)?experience"
    years_matches = re.finditer(years_pattern, text_lower, re.IGNORECASE)
    for match in years_matches:
        years = int(match.group(1))
        level = _determine_level_from_years(years)
        cues.append(
            SeniorityCue(
                level=level,
                years_experience=years,
                indicators=[match.group(0)],
                confidence=0.9,
            )
        )

    # Pattern: Title-based seniority
    title_patterns = {
        r"\bjunior\b": "junior",
        r"\bmid-level\b": "mid",
        r"\bmid level\b": "mid",
        r"\bsenior\b": "senior",
        r"\blead\b": "lead",
        r"\bprincipal\b": "principal",
        r"\bstaff\b": "staff",
        r"\barchitect\b": "senior",
    }

    for pattern, level in title_patterns.items():
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Check if we already have a cue for this level
            existing = next((c for c in cues if c.level == level), None)
            if existing:
                if match.group(0) not in existing.indicators:
                    existing.indicators.append(match.group(0))
            else:
                cues.append(
                    SeniorityCue(
                        level=level,
                        years_experience=None,
                        indicators=[match.group(0)],
                        confidence=0.8,
                    )
                )

    return cues


def _determine_level_from_years(years: int) -> str:
    """Determine seniority level based on years of experience."""
    if years < 2:
        return "junior"
    elif years < 5:
        return "mid"
    elif years < 8:
        return "senior"
    else:
        return "senior"  # Could be lead/principal but default to senior


def _deduplicate_skills(skills: list[HardSkill]) -> list[HardSkill]:
    """Deduplicate and merge skills with same normalized name."""
    skill_map: dict[str, HardSkill] = {}

    for skill in skills:
        key = skill.name.lower()
        if key in skill_map:
            # Merge with existing
            existing = skill_map[key]
            existing.mentions += skill.mentions
            existing.variations.extend([v for v in skill.variations if v not in existing.variations])
            # Keep higher confidence
            existing.confidence = max(existing.confidence, skill.confidence)
        else:
            skill_map[key] = skill

    return list(skill_map.values())


def _deduplicate_keywords(keywords: list[JDKeyword]) -> list[JDKeyword]:
    """Deduplicate keywords."""
    keyword_map: dict[str, JDKeyword] = {}

    for keyword in keywords:
        key = keyword.keyword.lower()
        if key in keyword_map:
            existing = keyword_map[key]
            existing.mentions += keyword.mentions
            existing.importance = max(existing.importance, keyword.importance)
        else:
            keyword_map[key] = keyword

    return list(keyword_map.values())

