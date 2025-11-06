import re
from typing import Dict, List

from rapidfuzz import fuzz

from minerva_models import Span
from minerva_backend.processing.models import EntityMapping


class SpanProcessingService:
    """Dedicated service for span processing."""

    def hydrate_spans_for_text(
        self, span_texts: List[str], entry_text: str
    ) -> List[Span]:
        """
        Given a list of span texts and entry text, returns hydrated Span objects.
        Uses exact and fuzzy phrase matches (no word-level fallback).
        """
        spans = []
        for span_text in span_texts:
            entry_text_lower = entry_text.lower()
            span_text_lower = span_text.lower()
            span_start = entry_text_lower.find(span_text_lower)
            if span_start != -1:
                span_end = span_start + len(span_text)
                actual_text = entry_text[span_start:span_end]
                spans.append(Span(start=span_start, end=span_end, text=actual_text))
            else:
                if " " in span_text:
                    best_phrase_match = self._find_best_phrase_match(
                        span_text, entry_text
                    )
                    if best_phrase_match:
                        phrase, start_pos, end_pos, score = best_phrase_match
                        spans.append(Span(start=start_pos, end=end_pos, text=phrase))
                        print(
                            f"Fuzzy phrase match found: '{span_text}' -> '{phrase}' (score: {score})"
                        )
                    else:
                        print(
                            f"Warning: No suitable phrase match found for span '{span_text}'"
                        )
                else:
                    print(
                        f"Warning: No exact match found for single-word span '{span_text}' and word-level fallback is disabled."
                    )
        return spans

    def process_spans(
        self, processed_entities: List[Dict], journal_entry
    ) -> List[EntityMapping]:
        """
        Process a list of dictionaries with 'entity' and 'spans', hydrate spans and return EntityMapping.
        """
        result: List[EntityMapping] = []
        for item in processed_entities:
            hydrated_spans = self.hydrate_spans_for_text(
                item["spans"], journal_entry.entry_text
            )
            if hydrated_spans:
                result.append(EntityMapping(item["entity"], hydrated_spans))
            else:
                print(f"Warning: No valid spans found for entity '{item['entity']}'")
        return result

    def _find_best_phrase_match(
        self, target_span: str, text: str, min_score: int = 75
    ) -> tuple | None:
        """
        Find the best phrase match in text using a sliding window approach.
        Returns (matched_phrase, start_pos, end_pos, score) or None if no good match found.
        """
        # Create word mappings that preserve original positions
        target_words = target_span.split()
        text_word_positions = []

        # Find each word and its position in the original text
        for match in re.finditer(r"\S+", text):
            text_word_positions.append(
                {"word": match.group(), "start": match.start(), "end": match.end()}
            )

        text_words: list[str] = [pos["word"] for pos in text_word_positions]

        if not target_words or not text_words:
            raise Exception("Target span or text is empty.")

        best_match = None
        best_score = 0.0

        # Try different window sizes around the target length
        for window_size in range(max(1, len(target_words) - 1), len(target_words) + 3):
            if window_size > len(text_words):
                break

            for i in range(len(text_words) - window_size + 1):
                window_words = text_words[i : i + window_size]
                window_phrase = " ".join(window_words)

                # Calculate similarity score
                score = fuzz.ratio(target_span.lower(), window_phrase.lower())

                if score > best_score and score >= min_score:
                    # Get positions from original text
                    start_pos = text_word_positions[i]["start"]
                    end_pos = text_word_positions[i + window_size - 1]["end"]

                    # Extract the actual matched phrase with original formatting/spacing
                    matched_phrase = text[start_pos:end_pos]
                    best_match = (matched_phrase, start_pos, end_pos, score)
                    best_score = score

        return best_match
