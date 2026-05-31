import sys
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple

# --- Data models ---------------------------------------------------

@dataclass
class Document:
    title: str
    content: str
    source_type: str  # e.g., 'SOP', 'Policy', 'CustomerRecord', 'Ticket'
    date: str  # ISO date string for recency ranking

@dataclass
class SearchResult:
    doc: Document
    overlap: int
    rank_score: float

@dataclass
class KnowledgeAnswer:
    answer: str
    citation: str

# --- Sample knowledge base -----------------------------------------

def load_sample_documents() -> List[Document]:
    """Return a small static list of sample documents."""
    docs = [
        Document(
            title="Employee Onboarding",
            content="Steps for onboarding a new employee: account creation, hardware provisioning, policy training, and first week schedule.",
            source_type="SOP",
            date="2023-05-12",
        ),
        Document(
            title="Vacation Request Policy",
            content="Employees may request vacation up to 30 days in advance via the HR portal. Managers approve within 5 business days.",
            source_type="Policy",
            date="2022-11-01",
        ),
        Document(
            title="Customer Issue 2024-03-15",
            content="Customer reported intermittent connectivity; resolved by resetting router and updating firmware.",
            source_type="Ticket",
            date="2024-03-16",
        ),
        Document(
            title="Data Retention Policy",
            content="All logs are retained for 90 days. Sensitive data is encrypted at rest.",
            source_type="Policy",
            date="2021-07-20",
        ),
        Document(
            title="Hardware Provisioning SOP",
            content="Guidelines for ordering, receiving, and configuring laptops, monitors, and peripherals.",
            source_type="SOP",
            date="2022-02-10",
        ),
        Document(
            title="Customer Contract ABC Corp",
            content="Service level agreement includes 99.9% uptime, quarterly business reviews, and escalation contacts.",
            source_type="CustomerRecord",
            date="2023-09-30",
        ),
    ]
    return docs

# --- Search logic ---------------------------------------------------

def keyword_overlap(query: str, text: str) -> int:
    q_words = set(re.findall(r"\w+", query.lower()))
    t_words = set(re.findall(r"\w+", text.lower()))
    return len(q_words & t_words)

def rank_results(results: List[SearchResult]) -> List[SearchResult]:
    # Higher overlap first, then source priority, then newer date
    source_priority = {"SOP": 4, "Policy": 3, "CustomerRecord": 2, "Ticket": 1}
    def sort_key(r: SearchResult):
        date_val = datetime.fromisoformat(r.doc.date).timestamp()
        return (-r.overlap, -source_priority.get(r.doc.source_type, 0), -date_val)
    return sorted(results, key=sort_key)

def search_knowledge_base(query: str, docs: List[Document]) -> List[SearchResult]:
    results = []
    for doc in docs:
        overlap = keyword_overlap(query, doc.content + " " + doc.title)
        if overlap > 0:
            results.append(SearchResult(doc=doc, overlap=overlap, rank_score=0))
    ranked = rank_results(results)
    # assign a simple score for demonstration
    for i, r in enumerate(ranked, start=1):
        r.rank_score = 1 / i
    return ranked

# --- Answer synthesis ----------------------------------------------

def synthesize_answer(query: str, results: List[SearchResult]) -> KnowledgeAnswer:
    if not results:
        return KnowledgeAnswer(answer="I couldn't find relevant information.", citation="")
    top = results[0].doc
    # simple snippet: first sentence containing any query word
    snippets = []
    query_words = set(re.findall(r"\w+", query.lower()))
    for sentence in re.split(r"[.!?]", top.content):
        if any(w in sentence.lower() for w in query_words):
            snippets.append(sentence.strip())
            break
    if not snippets:
        snippets.append(top.content.split(".")[0])
    answer = f"{snippets[0]}."
    citation = f"[{top.source_type}] {top.title} ({{top.date}})".replace("{top.date}", top.date)
    return KnowledgeAnswer(answer=answer, citation=citation)

# --- CLI entry point ------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 workflow.py \"your question\"")
        sys.exit(1)
    query = " ".join(sys.argv[1:])
    docs = load_sample_documents()
    results = search_knowledge_base(query, docs)
    ka = synthesize_answer(query, results)
    print("Answer:", ka.answer)
    if ka.citation:
        print("Citation:", ka.citation)

if __name__ == "__main__":
    main()
