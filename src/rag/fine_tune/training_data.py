"""Manual Q&A pair management for fine-tuning.

Provides JSON-based storage for hand-crafted question-answer pairs
with support for loading, merging, and categorizing.
"""
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default storage location
DEFAULT_MANUAL_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "rag" / "fine_tuning"

CATEGORIES = [
    "skill_inquiry",
    "job_search",
    "career_advice",
    "market_intelligence",
    "salary_compensation",
    "company_industry",
    "location_geography",
]

SYSTEM_PROMPT = """You are JobPulse Assistant, an AI helper for the African tech job market.
Answer questions about tech jobs, skills, careers, and market trends across Africa.
Use ONLY the provided context. Be concise, cite sources, and end with a practical recommendation."""


class TrainingDataManager:
    """Manage manual Q&A training pairs."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_MANUAL_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.pairs_file = self.data_dir / "manual_qa_pairs.json"
        self.pairs: list[dict] = self._load()

    def _load(self) -> list[dict]:
        """Load existing pairs from disk."""
        if self.pairs_file.exists():
            with open(self.pairs_file, "r") as f:
                return json.load(f)
        return []

    def save(self) -> None:
        """Save pairs to disk."""
        with open(self.pairs_file, "w") as f:
            json.dump(self.pairs, f, indent=2)
        logger.info("Saved %d manual pairs to %s", len(self.pairs), self.pairs_file)

    def add_pair(
        self,
        question: str,
        answer: str,
        category: str = "general",
        context: str = "",
        metadata: dict | None = None,
    ) -> dict:
        """Add a single Q&A pair."""
        if category not in CATEGORIES:
            logger.warning("Unknown category '%s', using 'general'", category)
            category = "general"

        pair = {
            "question": question.strip(),
            "answer": answer.strip(),
            "question_type": category,
            "context": context.strip(),
            "metadata": metadata or {},
            "source": "manual",
        }
        self.pairs.append(pair)
        return pair

    def add_batch(self, pairs: list[dict]) -> int:
        """Add multiple Q&A pairs. Each dict must have 'question' and 'answer'."""
        added = 0
        for pair in pairs:
            if "question" in pair and "answer" in pair:
                self.add_pair(
                    question=pair["question"],
                    answer=pair["answer"],
                    category=pair.get("category", "general"),
                    context=pair.get("context", ""),
                    metadata=pair.get("metadata", {}),
                )
                added += 1
        return added

    def remove_pair(self, index: int) -> bool:
        """Remove a pair by index."""
        if 0 <= index < len(self.pairs):
            self.pairs.pop(index)
            return True
        return False

    def get_by_category(self, category: str) -> list[dict]:
        """Get all pairs for a specific category."""
        return [p for p in self.pairs if p.get("question_type") == category]

    def get_statistics(self) -> dict[str, int]:
        """Get count of pairs per category."""
        stats = {cat: 0 for cat in CATEGORIES}
        for pair in self.pairs:
            cat = pair.get("question_type", "general")
            if cat in stats:
                stats[cat] += 1
        stats["total"] = len(self.pairs)
        return stats

    def to_chatml(self) -> list[dict]:
        """Convert manual pairs to ChatML format."""
        formatted = []
        for pair in self.pairs:
            context = pair.get("context", "")
            question = pair["question"]
            prompt = f"Context:\n{context}\n\n{question}" if context else question

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": pair["answer"]},
            ]
            formatted.append({
                "messages": messages,
                "question_type": pair.get("question_type", "general"),
            })
        return formatted

    def merge_with_auto(self, auto_pairs: list[dict]) -> list[dict]:
        """Merge manual pairs with auto-generated pairs."""
        manual_chatml = self.to_chatml()
        return manual_chatml + auto_pairs

    def export_for_training(self, output_path: Path) -> Path:
        """Export all pairs in ChatML format for training."""
        chatml_pairs = self.to_chatml()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(chatml_pairs, f, indent=2)

        logger.info("Exported %d pairs to %s", len(chatml_pairs), output_path)
        return output_path


# ---------------------------------------------------------------------------
# Sample manual Q&A pairs for bootstrapping
# ---------------------------------------------------------------------------

SAMPLE_MANUAL_PAIRS = [
    {
        "question": "What are the most in-demand tech skills in Kenya?",
        "answer": "Based on the JobPulse dataset, the most in-demand tech skills in Kenya include Python, JavaScript, React, Node.js, SQL, and cloud platforms like AWS. These skills appear across software engineering, data science, and DevOps roles. Focus on these core skills to maximize your job opportunities.",
        "category": "market_intelligence",
    },
    {
        "question": "How do I become a data scientist in Africa?",
        "answer": "To become a data scientist in Africa, focus on building these skills: Python, R, SQL, Machine Learning (TensorFlow/PyTorch), Statistics, and Data Visualization. Start with online courses, build projects using real datasets, and contribute to open-source. The JobPulse dataset shows demand for data scientists across Kenya, Nigeria, and South Africa.",
        "category": "career_advice",
    },
    {
        "question": "What companies are hiring remote developers in Nigeria?",
        "answer": "Several companies in Nigeria are hiring remote developers. Based on the JobPulse dataset, opportunities exist at both local startups and international companies with remote-friendly policies. Focus on roles requiring Python, JavaScript, and cloud skills. Build a strong technical foundation. Consider bootcamps or certifications in cloud platforms (AWS, Azure) to stand out. Network with the local tech community through meetups and conferences.",
        "category": "career_advice",
    },
    {
        "question": "Is Python still relevant for backend development in 2024?",
        "answer": "Yes, Python remains highly relevant for backend development. It's used in web frameworks (Django, Flask, FastAPI), data science, machine learning, and automation. The JobPulse dataset shows Python as one of the top requested skills across African tech jobs, especially in data science and backend roles.",
        "category": "skill_inquiry",
    },
    {
        "question": "What is the salary range for software engineers in South Africa?",
        "answer": "Salary data in the JobPulse dataset is limited, but software engineer salaries in South Africa typically range from ZAR 300,000 to ZAR 900,000 annually depending on experience and company. Senior roles at established companies can exceed ZAR 1,000,000. Remote positions for international companies often pay higher rates.",
        "category": "salary_compensation",
    },
    {
        "question": "Which tech hubs are growing in East Africa?",
        "answer": "East Africa's tech ecosystem is growing rapidly, particularly in Kenya (Nairobi), Uganda (Kampala), and Rwanda (Kigali). Nairobi is known as 'Silicon Savannah' with a thriving startup ecosystem. Key areas include fintech, agritech, and healthtech. The JobPulse dataset shows increasing job opportunities across these locations.",
        "category": "location_geography",
    },
    {
        "question": "What does a senior DevOps engineer do?",
        "answer": "A senior DevOps engineer manages infrastructure automation, CI/CD pipelines, cloud architecture, and system reliability. Key skills include Docker, Kubernetes, AWS/Azure/GCP, Terraform, and Linux. They lead DevOps practices, mentor junior engineers, and ensure system scalability and security.",
        "category": "career_advice",
    },
    {
        "question": "What skills do I need for a cloud architect role?",
        "answer": "Cloud architects need expertise in cloud platforms (AWS, Azure, GCP), infrastructure-as-code (Terraform, CloudFormation), containerization (Docker, Kubernetes), networking, security, and cost optimization. Certifications like AWS Solutions Architect or Azure Architect can validate your skills and improve job prospects.",
        "category": "skill_inquiry",
    },
]


def load_sample_manual_pairs() -> list[dict]:
    """Return sample manual pairs for bootstrapping."""
    return SAMPLE_MANUAL_PAIRS.copy()
