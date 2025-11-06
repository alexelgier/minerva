"""
Unit tests for MergeConceptPrompt.

Tests the concept merging prompt functionality.
"""

import pytest
from pydantic import ValidationError

from minerva_backend.prompt.merge_concept import MergeConceptPrompt, MergedConcept


class TestMergedConcept:
    """Test MergedConcept model."""
    
    def test_valid_merged_concept(self):
        """Test creating a valid merged concept."""
        concept = MergedConcept(
            title="Test Concept",
            concept="A test concept definition",
            analysis="Analysis of the test concept",
            source="Test source",
            summary_short="Short summary",
            summary="Detailed summary of the test concept"
        )
        
        assert concept.title == "Test Concept"
        assert concept.concept == "A test concept definition"
        assert concept.analysis == "Analysis of the test concept"
        assert concept.source == "Test source"
        assert concept.summary_short == "Short summary"
        assert concept.summary == "Detailed summary of the test concept"
    
    def test_merged_concept_with_none_source(self):
        """Test creating a merged concept with None source."""
        concept = MergedConcept(
            title="Test Concept",
            concept="A test concept definition",
            analysis="Analysis of the test concept",
            source=None,
            summary_short="Short summary",
            summary="Detailed summary of the test concept"
        )
        
        assert concept.source is None
    
    def test_merged_concept_validation_error(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError):
            MergedConcept(
                title="Test Concept",
                # Missing required fields
            )


class TestMergeConceptPrompt:
    """Test MergeConceptPrompt class."""
    
    def test_response_model(self):
        """Test that response_model returns MergedConcept."""
        prompt = MergeConceptPrompt()
        assert prompt.response_model() == MergedConcept
    
    def test_system_prompt(self):
        """Test system prompt content."""
        prompt = MergeConceptPrompt()
        system_prompt = prompt.system_prompt()
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert "fusionar información de conceptos" in system_prompt
        assert "MÁXIMO 100 palabras" in system_prompt
        assert "MÁXIMO 30 palabras" in system_prompt
    
    def test_user_prompt(self):
        """Test user prompt generation."""
        prompt = MergeConceptPrompt()
        
        test_data = {
            "entity_name": "Test Concept",
            "existing_title": "Existing Title",
            "existing_concept": "Existing concept definition",
            "existing_analysis": "Existing analysis",
            "existing_source": "Existing source",
            "existing_short_summary": "Existing short summary",
            "existing_summary": "Existing detailed summary",
            "new_title": "New Title",
            "new_concept": "New concept definition",
            "new_analysis": "New analysis",
            "new_source": "New source",
            "new_short_summary": "New short summary",
            "new_summary": "New detailed summary"
        }
        
        user_prompt = prompt.user_prompt(test_data)
        
        assert isinstance(user_prompt, str)
        assert len(user_prompt) > 0
        assert "Test Concept" in user_prompt
        assert "Existing Title" in user_prompt
        assert "New Title" in user_prompt
        assert "CONCEPTO EXISTENTE:" in user_prompt
        assert "CONCEPTO EXTRAÍDO:" in user_prompt
    
    def test_user_prompt_with_none_values(self):
        """Test user prompt with None values."""
        prompt = MergeConceptPrompt()
        
        test_data = {
            "entity_name": "Test Concept",
            "existing_title": "Existing Title",
            "existing_concept": "Existing concept definition",
            "existing_analysis": "Existing analysis",
            "existing_source": None,
            "existing_short_summary": "Existing short summary",
            "existing_summary": "Existing detailed summary",
            "new_title": "New Title",
            "new_concept": "New concept definition",
            "new_analysis": "New analysis",
            "new_source": None,
            "new_short_summary": "New short summary",
            "new_summary": "New detailed summary"
        }
        
        user_prompt = prompt.user_prompt(test_data)
        
        assert isinstance(user_prompt, str)
        assert "None" in user_prompt  # None values should be displayed as "None"
    
    def test_user_prompt_empty_data(self):
        """Test user prompt with empty data."""
        prompt = MergeConceptPrompt()
        
        test_data = {
            "entity_name": "",
            "existing_title": "",
            "existing_concept": "",
            "existing_analysis": "",
            "existing_source": "",
            "existing_short_summary": "",
            "existing_summary": "",
            "new_title": "",
            "new_concept": "",
            "new_analysis": "",
            "new_source": "",
            "new_short_summary": "",
            "new_summary": ""
        }
        
        user_prompt = prompt.user_prompt(test_data)
        
        assert isinstance(user_prompt, str)
        assert len(user_prompt) > 0
        assert "CONCEPTO EXISTENTE:" in user_prompt
        assert "CONCEPTO EXTRAÍDO:" in user_prompt
