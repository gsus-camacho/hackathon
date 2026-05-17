"""Type aliases for recommendations."""
from typing import Literal

Focus = Literal["revenue", "nutrition", "safety", "general"]
RecommendationKind = Literal["product", "package", "nutrition", "operational"]
