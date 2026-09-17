from __future__ import annotations

import math
import re
from collections import Counter

from .models import SearchResult
from .storage import Storage

LATIN_TOKEN = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)*", re.IGNORECASE)
CJK_CHAR = re.compile(r"[\u3400-\u9fff]")


def tokenize(text: str) -> list[str]:
    lowered = text.casefold()
    latin = LATIN_TOKEN.findall(lowered)
    chars = CJK_CHAR.findall(lowered)
    cjk_bigrams = ["".join(chars[index : index + 2]) for index in range(len(chars) - 1)]
    cjk_trigrams = ["".join(chars[index : index + 3]) for index in range(len(chars) - 2)]
    if len(chars) == 1:
        return latin + chars
    return latin + cjk_bigrams + cjk_trigrams


class RetrievalService:
    def __init__(self, storage: Storage):
        self.storage = storage

    def search(self, query: str, *, top_k: int = 5, min_score: float = 0.04) -> list[SearchResult]:
        chunks = self.storage.all_chunks()
        query_tokens = tokenize(query)
        if not chunks or not query_tokens:
            return []

        query_counts = Counter(query_tokens)
        document_tokens = [Counter(tokenize(chunk["text"])) for chunk in chunks]
        document_frequency: Counter[str] = Counter()
        for counts in document_tokens:
            document_frequency.update(counts.keys())

        total = len(chunks)
        normalized_query = "".join(query.casefold().split())
        scored: list[SearchResult] = []
        for chunk, counts in zip(chunks, document_tokens, strict=True):
            weighted_match = 0.0
            maximum = 0.0
            for token, query_frequency in query_counts.items():
                inverse_frequency = math.log((total + 1) / (document_frequency[token] + 1)) + 1
                maximum += inverse_frequency * query_frequency
                if token in counts:
                    weighted_match += inverse_frequency * min(counts[token], 3) * query_frequency

            score = weighted_match / maximum if maximum else 0.0
            normalized_text = "".join(str(chunk["text"]).casefold().split())
            if len(normalized_query) >= 4 and normalized_query in normalized_text:
                score += 0.35
            if score < min_score:
                continue
            scored.append(
                SearchResult(
                    chunk_id=chunk["chunk_id"],
                    url=chunk["url"],
                    page_title=chunk["page_title"],
                    section_title=chunk["section_title"],
                    text=chunk["text"],
                    score=round(score, 4),
                )
            )

        scored.sort(key=lambda result: result.score, reverse=True)
        return scored[:top_k]
