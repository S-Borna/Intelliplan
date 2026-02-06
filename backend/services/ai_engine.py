"""
AI Engine — Core intelligence for Intelliplan.

Provides NLP analysis, context enrichment, and decision support.
Uses rule-based logic with optional LLM (OpenAI) enhancement.
"""

import json
import re
from datetime import datetime, timezone

from backend.config import settings

# ── Skill taxonomy for matching ────────────────────────

SKILL_CATEGORIES = {
    "backend": ["python", "java", "c#", ".net", "node.js", "go", "rust", "php", "ruby", "scala", "kotlin"],
    "frontend": ["react", "angular", "vue", "svelte", "typescript", "javascript", "html", "css", "next.js"],
    "data": ["sql", "python", "r", "spark", "hadoop", "etl", "power bi", "tableau", "pandas", "numpy"],
    "devops": ["docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ci/cd", "jenkins", "github actions"],
    "mobile": ["swift", "kotlin", "react native", "flutter", "ios", "android"],
    "ai_ml": ["machine learning", "deep learning", "nlp", "pytorch", "tensorflow", "llm", "computer vision"],
    "management": ["projektledning", "scrum", "agile", "pm", "product owner", "scrum master"],
    "design": ["ux", "ui", "figma", "sketch", "design system", "user research"],
}

PRIORITY_KEYWORDS = {
    "urgent": ["akut", "omedelbart", "brådskande", "critical", "urgent", "asap", "idag"],
    "high": ["snabbt", "prioritet", "viktig", "snarast", "hög prioritet", "important"],
    "medium": ["planerad", "kommande", "nästa månad"],
    "low": ["framtida", "eventuellt", "utforska", "kanske"],
}


class AIEngine:
    """Core AI engine for request analysis and decision support."""

    def analyze_request(self, title: str, description: str, skills: list[str] | None = None) -> dict:
        """
        Analyze a customer request and return AI-enriched data.

        Returns:
            dict with keys: summary, category, complexity_score, extracted_skills,
                           detected_priority, insights
        """
        text = f"{title} {description}".lower()

        # Extract & categorize skills
        detected_skills = self._extract_skills(text, skills or [])
        category = self._categorize_request(detected_skills, text)
        priority = self._detect_priority(text)
        complexity = self._calculate_complexity(text, detected_skills)
        summary = self._generate_summary(title, description, detected_skills, category)
        insights = self._generate_insights(text, detected_skills, complexity)

        return {
            "summary": summary,
            "category": category,
            "complexity_score": complexity,
            "extracted_skills": detected_skills,
            "detected_priority": priority,
            "insights": insights,
        }

    def _extract_skills(self, text: str, provided_skills: list[str]) -> list[str]:
        """Extract skills from text and merge with provided skills."""
        found = set(s.lower().strip() for s in provided_skills)

        for category, skills in SKILL_CATEGORIES.items():
            for skill in skills:
                if skill.lower() in text:
                    found.add(skill)

        # Also detect years of experience patterns
        exp_pattern = r"(\d+)\+?\s*(?:års?|years?)\s*(?:erfarenhet|experience)"
        matches = re.findall(exp_pattern, text)
        if matches:
            found.add(f"{matches[0]}+ years experience")

        return sorted(found)

    def _categorize_request(self, skills: list[str], text: str) -> str:
        """Categorize the request based on skills and description."""
        category_scores: dict[str, int] = {}

        for category, cat_skills in SKILL_CATEGORIES.items():
            score = sum(1 for s in skills if s in cat_skills)
            if score > 0:
                category_scores[category] = score

        if not category_scores:
            # Fallback: check text for category hints
            if any(w in text for w in ["utvecklare", "developer", "programmera", "kod"]):
                return "development"
            if any(w in text for w in ["test", "qa", "quality"]):
                return "testing"
            if any(w in text for w in ["projekt", "project", "leda", "manage"]):
                return "management"
            return "general"

        return max(category_scores, key=category_scores.get)

    def _detect_priority(self, text: str) -> str:
        """Detect priority from natural language."""
        for priority, keywords in PRIORITY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return priority
        return "medium"

    def _calculate_complexity(self, text: str, skills: list[str]) -> float:
        """Calculate complexity score 0-1 based on requirements."""
        score = 0.3  # Base

        # More skills = more complex
        score += min(len(skills) * 0.08, 0.3)

        # Long descriptions suggest complexity
        word_count = len(text.split())
        if word_count > 200:
            score += 0.15
        elif word_count > 100:
            score += 0.1

        # Multi-person requests
        numbers = re.findall(r"(\d+)\s*(?:konsulter|consultants|personer|people|resources)", text)
        if numbers and int(numbers[0]) > 2:
            score += 0.15

        # Niche skills increase complexity
        niche_skills = {"rust", "scala", "computer vision", "deep learning", "flutter"}
        if any(s in niche_skills for s in skills):
            score += 0.1

        return min(round(score, 2), 1.0)

    def _generate_summary(self, title: str, description: str, skills: list[str], category: str) -> str:
        """Generate a concise AI summary of the request."""
        skills_str = ", ".join(skills[:5]) if skills else "general skills"
        return (
            f"Request for {category} resources with focus on {skills_str}. "
            f"{title.rstrip('.')}. "
            f"{'Complex multi-skill requirement.' if len(skills) > 3 else 'Focused skill requirement.'}"
        )

    def _generate_insights(self, text: str, skills: list[str], complexity: float) -> list[str]:
        """Generate actionable insights for the consultant manager."""
        insights = []

        if complexity > 0.7:
            insights.append("⚠️ High complexity — consider splitting into multiple assignments")
        if complexity < 0.3:
            insights.append("✅ Straightforward request — quick matching likely possible")

        if len(skills) > 5:
            insights.append("🔍 Many required skills — a senior/lead profile may be needed")

        niche = [s for s in skills if s in {"rust", "scala", "computer vision", "deep learning", "flutter"}]
        if niche:
            insights.append(f"💎 Niche skills detected ({', '.join(niche)}) — limited pool expected")

        if any(w in text for w in ["remote", "distans"]):
            insights.append("🌍 Remote work possible — expands candidate pool")

        if any(w in text for w in ["akut", "urgent", "asap", "brådskande"]):
            insights.append("🚨 Urgent request — prioritize immediate availability matching")

        if not insights:
            insights.append("📋 Standard request — proceed with normal matching workflow")

        return insights

    def generate_recommendations(self, assessment_data: dict) -> list[str]:
        """Generate decision recommendations based on feasibility assessment."""
        recommendations = []
        overall = assessment_data.get("overall_rating", "medium")
        scores = {
            "availability": assessment_data.get("availability_score", 50),
            "skills": assessment_data.get("skills_match_score", 50),
            "budget": assessment_data.get("budget_fit_score", 50),
            "timeline": assessment_data.get("timeline_score", 50),
            "compliance": assessment_data.get("compliance_score", 50),
        }

        if overall == "high":
            recommendations.append("✅ Strong match — recommend proceeding with top candidates immediately")
        elif overall == "not_feasible":
            recommendations.append("❌ Cannot fulfill as specified — present alternatives to customer")

        if scores["availability"] < 40:
            recommendations.append("📅 Low availability — suggest alternative start dates or part-time arrangements")

        if scores["skills"] < 50:
            recommendations.append("🎓 Partial skills match — consider consultants with growth potential or training")

        if scores["budget"] < 40:
            recommendations.append("💰 Budget constraint — discuss rate adjustments or scope reduction with customer")

        if scores["compliance"] < 60:
            recommendations.append("⚖️ Compliance concerns — review contract terms and regulatory requirements")

        if scores["timeline"] < 50:
            recommendations.append("⏰ Tight timeline — consider phased staffing approach")

        if not recommendations:
            recommendations.append("👍 Balanced assessment — proceed with standard matching process")

        return recommendations


# Singleton
ai_engine = AIEngine()
