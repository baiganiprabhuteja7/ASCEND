from app.schemas import ChallengeRead


DEMO_CHALLENGES = [
    ChallengeRead(
        id="curious-observation",
        category="LEARN",
        title="A week of curious observation",
        description=(
            "Spend a little time noticing the nature, people, and needs around you. "
            "Capture one thing you learned each day."
        ),
        duration="7 days",
        level="Gentle start",
    ),
    ChallengeRead(
        id="share-a-skill",
        category="MAKE",
        title="Share one useful skill",
        description=(
            "Choose something you know and find a small, thoughtful way to share "
            "it with someone or a community you care about."
        ),
        duration="2 weeks",
        level="Make it yours",
    ),
    ChallengeRead(
        id="local-changemakers",
        category="CONNECT",
        title="Meet your local changemakers",
        description=(
            "Explore an issue that matters to you and learn about the people "
            "already doing good work in your community."
        ),
        duration="3 weeks",
        level="Explore at your pace",
    ),
]
