"""AI Research Service – generates original video ideas using the LLM."""
import json
import re
from typing import List
from app.services.ai.factory import get_llm_provider
from app.schemas.video_idea import VideoIdeaCreate
from app.models.video_idea import AgeCategory, ContentCategory

RESEARCH_SYSTEM = """
You are a creative content researcher for TinyTales World, an original children's
educational animation channel. Your role is to generate fresh, original video ideas.

RULES:
- Do NOT copy or reference Cocomelon, Pinkfong, or any existing show characters/songs.
- All content must be appropriate for children (ages 0-12).
- Each idea must be educational AND entertaining.
- Create original character concepts unique to TinyTales World.
- Ensure high educational value.
"""

IDEA_PROMPT = """
Generate {count} original children's video ideas for TinyTales World.

Focus categories: {categories}
Target ages: {ages}
Keywords to explore: {keywords}

Return a JSON array with exactly {count} objects, each with these fields:
- title: string (catchy, original, 5-10 words)
- concept: string (2-3 sentences describing the story/content)
- educational_value: string (what children will learn)
- age_category: one of "0-2", "3-5", "6-8", "9-12"
- content_category: one of nursery_rhyme, educational, animal_story, bedtime_story,
  alphabet, numbers, colors, shapes, seasons, holiday, adventure, friendship, science, music
- estimated_duration_minutes: number (1-10)
- keywords: list of 3-5 string tags
- originality_notes: string (what makes this unique)
- estimated_cost_usd: number (rough estimate in USD, typically 10-50)

Return ONLY the JSON array, no other text.
"""


class ResearchService:
    def __init__(self):
        self._llm = get_llm_provider()

    async def generate_ideas(
        self,
        count: int = 5,
        categories: List[ContentCategory] | None = None,
        age_categories: List[AgeCategory] | None = None,
        keywords: List[str] | None = None,
    ) -> tuple[List[VideoIdeaCreate], float]:
        cats = ", ".join(c.value for c in categories) if categories else "any"
        ages = ", ".join(a.value for a in age_categories) if age_categories else "0-12"
        kws = ", ".join(keywords) if keywords else "learning, fun, adventure"

        prompt = IDEA_PROMPT.format(count=count, categories=cats, ages=ages, keywords=kws)
        response = await self._llm.generate(prompt, system=RESEARCH_SYSTEM, max_tokens=4000)

        ideas = self._parse_ideas(response.content)
        return ideas, response.cost_usd

    def _parse_ideas(self, content: str) -> List[VideoIdeaCreate]:
        # Strip markdown code fences if present
        content = re.sub(r"```json\s*|\s*```", "", content).strip()
        try:
            raw = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON array
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if not match:
                return []
            raw = json.loads(match.group())

        ideas = []
        for item in raw:
            try:
                idea = VideoIdeaCreate(
                    title=item.get("title", "Untitled"),
                    concept=item.get("concept", ""),
                    educational_value=item.get("educational_value"),
                    age_category=item.get("age_category", "3-5"),
                    content_category=item.get("content_category", "educational"),
                    estimated_duration_minutes=float(item.get("estimated_duration_minutes", 3)),
                    keywords=item.get("keywords"),
                )
                ideas.append(idea)
            except Exception:
                continue
        return ideas
