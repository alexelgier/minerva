"""
Unit tests for document models.

Tests the JournalEntry class and its parsing methods with comprehensive coverage.
"""

import pytest
from datetime import date, datetime, time, timedelta
from minerva_backend.graph.models.documents import JournalEntry, Span, Chunk
from minerva_backend.graph.models.base import LexicalType


class TestJournalEntryParsing:
    """Test JournalEntry parsing functionality."""

    @pytest.fixture
    def sample_journal_text(self):
        """Sample journal text with all sections."""
        return """
Today I had a great day at work. I felt productive and accomplished.

## PANAS
### Positive Affect
Interested:: 4
Excited:: 3
Strong:: 5
Enthusiastic:: 4
Proud:: 5
Alert:: 4
Inspired:: 3
Determined:: 5
Attentive:: 4
Active:: 4

### Negative Affect
Distressed:: 1
Upset:: 1
Guilty:: 2
Scared:: 1
Hostile:: 1
Irritable:: 2
Ashamed:: 1
Nervous:: 2
Jittery:: 1
Afraid:: 1

## BPNS
### Autonomy
I feel like I can make choices about the things I do:: 4
I feel free to decide how I do my daily tasks:: 4

### Competence
I feel capable at the things I do:: 5
I can successfully complete challenging tasks:: 4

### Relatedness
I feel close and connected with the people around me:: 3
I get along well with the people I interact with daily:: 4
I feel supported by others in my life:: 4

## Flourishing Scale
I lead a purposeful and meaningful life:: 4
My social relationships are supportive and rewarding:: 4
I am engaged and interested in my daily activities:: 5
I actively contribute to the happiness and well-being of others:: 3
I am competent and capable in the activities that are important to me:: 4
I am a good person and live a good life:: 4
I am optimistic about my future:: 5
People respect me:: 4

Wake time: 07:30
Bedtime: 23:00

---
- Imagen, Detalle: Some additional notes
"""

    @pytest.fixture
    def minimal_journal_text(self):
        """Minimal journal text with only narration."""
        return "Today I went to the park with John. It was a beautiful day."

    def test_parse_complete_journal_entry(self, sample_journal_text):
        """Test parsing a complete journal entry with all sections."""
        journal_entry = JournalEntry.from_text(sample_journal_text, "2024-01-15")
        
        # Test basic properties
        assert journal_entry.uuid == "2024-01-15"
        assert journal_entry.date == date(2024, 1, 15)
        assert journal_entry.text == sample_journal_text
        assert journal_entry.type == LexicalType.JOURNAL_ENTRY.value
        
        # Test PANAS positive scores
        assert journal_entry.panas_pos == [4, 3, 5, 4, 5, 4, 3, 5, 4, 4]
        
        # Test PANAS negative scores
        assert journal_entry.panas_neg == [1, 1, 2, 1, 1, 2, 1, 2, 1, 1]
        
        # Test BPNS scores
        assert journal_entry.bpns == [4, 4, 5, 4, 3, 4, 4]
        
        # Test Flourishing scores
        assert journal_entry.flourishing == [4, 4, 5, 3, 4, 4, 5, 4]
        
        # Test wake/sleep times
        assert journal_entry.wake == datetime(2024, 1, 15, 7, 30)
        assert journal_entry.sleep == datetime(2024, 1, 15, 23, 0)
        
        # Test narration text
        assert "Today I had a great day at work" in journal_entry.entry_text

    def test_parse_minimal_journal_entry(self, minimal_journal_text):
        """Test parsing a minimal journal entry with only narration."""
        journal_entry = JournalEntry.from_text(minimal_journal_text, "2024-01-15")
        
        # Test basic properties
        assert journal_entry.uuid == "2024-01-15"
        assert journal_entry.date == date(2024, 1, 15)
        assert journal_entry.text == minimal_journal_text
        
        # Test that optional fields are None
        assert journal_entry.panas_pos is None
        assert journal_entry.panas_neg is None
        assert journal_entry.bpns is None
        assert journal_entry.flourishing is None
        assert journal_entry.wake is None
        assert journal_entry.sleep is None
        
        # Test narration text (should be None for minimal text without delimiters)
        assert journal_entry.entry_text is None

    def test_parse_date_format(self):
        """Test parsing different date formats."""
        text = "Today was a good day."
        
        # Test valid date
        journal_entry = JournalEntry.from_text(text, "2024-01-15")
        assert journal_entry.date == date(2024, 1, 15)
        
        # Test date with leading zeros
        journal_entry = JournalEntry.from_text(text, "2024-01-05")
        assert journal_entry.date == date(2024, 1, 5)

    def test_parse_wake_sleep_times(self):
        """Test parsing wake and sleep times."""
        text = """
Today was a good day.
Wake time: 08:00
Bedtime: 22:30
"""
        journal_entry = JournalEntry.from_text(text, "2024-01-15")
        
        assert journal_entry.wake == datetime(2024, 1, 15, 8, 0)
        assert journal_entry.sleep == datetime(2024, 1, 15, 22, 30)

    def test_parse_wake_sleep_cross_midnight(self):
        """Test parsing wake and sleep times that cross midnight."""
        text = """
Today was a good day.
Wake time: 08:00
Bedtime: 02:30
"""
        journal_entry = JournalEntry.from_text(text, "2024-01-15")
        
        assert journal_entry.wake == datetime(2024, 1, 15, 8, 0)
        assert journal_entry.sleep == datetime(2024, 1, 16, 2, 30)  # Next day

    def test_parse_partial_scores(self):
        """Test parsing journal entry with only some score sections."""
        text = """
Today was a good day.

## PANAS
### Positive Affect
Interested:: 4
Excited:: 3
Strong:: 5
Enthusiastic:: 4
Proud:: 5
Alert:: 4
Inspired:: 3
Determined:: 5
Attentive:: 4
Active:: 4

Wake time: 08:00
Bedtime: 22:30
"""
        journal_entry = JournalEntry.from_text(text, "2024-01-15")
        
        # Test that only available scores are parsed
        assert journal_entry.panas_pos == [4, 3, 5, 4, 5, 4, 3, 5, 4, 4]
        assert journal_entry.panas_neg is None
        assert journal_entry.bpns is None
        assert journal_entry.flourishing is None
        assert journal_entry.wake == datetime(2024, 1, 15, 8, 0)
        assert journal_entry.sleep == datetime(2024, 1, 15, 22, 30)


class TestJournalEntryHelperMethods:
    """Test JournalEntry helper parsing methods."""

    def test_parse_panas_positive(self):
        """Test parsing PANAS positive scores."""
        text = """
## PANAS
### Positive Affect
Interested:: 4
Excited:: 3
Strong:: 5
Enthusiastic:: 4
Proud:: 5
Alert:: 4
Inspired:: 3
Determined:: 5
Attentive:: 4
Active:: 4
"""
        result = JournalEntry._parse_panas_positive(text)
        assert result == {"panas_pos": [4, 3, 5, 4, 5, 4, 3, 5, 4, 4]}

    def test_parse_panas_positive_not_found(self):
        """Test parsing PANAS positive scores when not present."""
        text = "Today was a good day."
        result = JournalEntry._parse_panas_positive(text)
        assert result == {}

    def test_parse_panas_negative(self):
        """Test parsing PANAS negative scores."""
        text = """
### Negative Affect
Distressed:: 1
Upset:: 1
Guilty:: 2
Scared:: 1
Hostile:: 1
Irritable:: 2
Ashamed:: 1
Nervous:: 2
Jittery:: 1
Afraid:: 1
"""
        result = JournalEntry._parse_panas_negative(text)
        assert result == {"panas_neg": [1, 1, 2, 1, 1, 2, 1, 2, 1, 1]}

    def test_parse_bpns(self):
        """Test parsing BPNS scores."""
        text = """
## BPNS
### Autonomy
I feel like I can make choices about the things I do:: 4
I feel free to decide how I do my daily tasks:: 4

### Competence
I feel capable at the things I do:: 5
I can successfully complete challenging tasks:: 4

### Relatedness
I feel close and connected with the people around me:: 3
I get along well with the people I interact with daily:: 4
I feel supported by others in my life:: 4
"""
        result = JournalEntry._parse_bpns(text)
        assert result == {"bpns": [4, 4, 5, 4, 3, 4, 4]}

    def test_parse_flourishing(self):
        """Test parsing Flourishing Scale scores."""
        text = """
## Flourishing Scale
I lead a purposeful and meaningful life:: 4
My social relationships are supportive and rewarding:: 4
I am engaged and interested in my daily activities:: 5
I actively contribute to the happiness and well-being of others:: 3
I am competent and capable in the activities that are important to me:: 4
I am a good person and live a good life:: 4
I am optimistic about my future:: 5
People respect me:: 4
"""
        result = JournalEntry._parse_flourishing(text)
        assert result == {"flourishing": [4, 4, 5, 3, 4, 4, 5, 4]}

    def test_parse_date(self):
        """Test parsing date from string."""
        result = JournalEntry._parse_date("2024-01-15")
        assert result == {"date": date(2024, 1, 15)}

    def test_parse_wake_sleep(self):
        """Test parsing wake and sleep times."""
        text = "Wake time: 08:00\nBedtime: 22:30"
        base_date = date(2024, 1, 15)
        
        result = JournalEntry._parse_wake_sleep(text, base_date)
        
        assert result["wake"] == datetime(2024, 1, 15, 8, 0)
        assert result["sleep"] == datetime(2024, 1, 15, 22, 30)

    def test_parse_wake_sleep_not_found(self):
        """Test parsing wake and sleep times when not present."""
        text = "Today was a good day."
        base_date = date(2024, 1, 15)
        
        result = JournalEntry._parse_wake_sleep(text, base_date)
        assert result == {}

    def test_parse_narration(self):
        """Test parsing narration text."""
        text = """
Today I had a great day at work. I felt productive and accomplished.

---
- Imagen, Detalle: Some additional notes
"""
        result = JournalEntry._parse_narration(text)
        assert "Today I had a great day at work" in result["text"]

    def test_parse_narration_not_found(self):
        """Test parsing narration text when not present."""
        text = "## PANAS\nInterested:: 4"
        result = JournalEntry._parse_narration(text)
        assert result == {}


class TestJournalEntryValidation:
    """Test JournalEntry validation and edge cases."""

    def test_journal_entry_creation(self):
        """Test creating a JournalEntry with all fields."""
        journal_entry = JournalEntry(
            uuid="2024-01-15",
            date=date(2024, 1, 15),
            text="Today was a good day.",
            entry_text="Today was a good day.",
            panas_pos=[4, 3, 5, 4, 5, 4, 3, 5, 4, 4],
            panas_neg=[1, 1, 2, 1, 1, 2, 1, 2, 1, 1],
            bpns=[4, 4, 5, 4, 3, 4, 4],
            flourishing=[4, 4, 5, 3, 4, 4, 5, 4],
            wake=datetime(2024, 1, 15, 8, 0),
            sleep=datetime(2024, 1, 15, 22, 30)
        )
        
        assert journal_entry.uuid == "2024-01-15"
        assert journal_entry.date == date(2024, 1, 15)
        assert journal_entry.type == LexicalType.JOURNAL_ENTRY.value

    def test_journal_entry_minimal_creation(self):
        """Test creating a minimal JournalEntry."""
        journal_entry = JournalEntry(
            uuid="2024-01-15",
            date=date(2024, 1, 15),
            text="Today was a good day."
        )
        
        assert journal_entry.uuid == "2024-01-15"
        assert journal_entry.date == date(2024, 1, 15)
        assert journal_entry.text == "Today was a good day."
        assert journal_entry.entry_text is None
        assert journal_entry.panas_pos is None
        assert journal_entry.panas_neg is None
        assert journal_entry.bpns is None
        assert journal_entry.flourishing is None
        assert journal_entry.wake is None
        assert journal_entry.sleep is None


class TestSpan:
    """Test Span document model."""

    def test_span_creation(self):
        """Test creating a Span."""
        span = Span(
            uuid="span-1",
            text="John",
            start=10,
            end=14
        )
        
        assert span.uuid == "span-1"
        assert span.text == "John"
        assert span.start == 10
        assert span.end == 14
        assert span.type == LexicalType.SPAN.value

    def test_span_validation(self):
        """Test Span validation."""
        # Valid span
        span = Span(
            uuid="span-1",
            text="John",
            start=10,
            end=14
        )
        assert span.start < span.end
        
        # Test that end is exclusive
        assert span.text == "John"  # 4 characters
        assert span.end - span.start == 4


class TestChunk:
    """Test Chunk document model."""

    def test_chunk_creation_with_uuid(self):
        """Test creating a Chunk with provided UUID."""
        chunk = Chunk(
            text="This is a chunk of text.",
            uuid="chunk-123"
        )
        
        assert chunk.uuid == "chunk-123"
        assert chunk.text == "This is a chunk of text."
        assert chunk.type == LexicalType.CHUNK.value

    def test_chunk_creation_without_uuid(self):
        """Test creating a Chunk without UUID (auto-generated)."""
        chunk = Chunk(text="This is a chunk of text.")
        
        assert chunk.uuid is not None
        assert chunk.text == "This is a chunk of text."
        assert chunk.type == LexicalType.CHUNK.value

    def test_chunk_creation_with_kwargs(self):
        """Test creating a Chunk with additional keyword arguments."""
        chunk = Chunk(
            text="This is a chunk of text.",
            uuid="chunk-123"
        )
        
        assert chunk.uuid == "chunk-123"
        assert chunk.text == "This is a chunk of text."
