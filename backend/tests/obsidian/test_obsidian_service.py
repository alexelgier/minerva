import os
import pytest
import yaml
from minerva_backend.obsidian.obsidian_service import ObsidianService


@pytest.fixture
def obsidian_service(tmp_path):
    """Fixture to create an ObsidianService with a temporary vault."""
    vault_path = tmp_path

    # Create some files and directories
    (vault_path / "note_with_frontmatter.md").write_text(
        "---\n"
        "entity_id: '123'\n"
        "entity_type: test\n"
        "aliases:\n"
        "  - test_alias\n"
        "short_summary: A test note.\n"
        "---\n"
        "Body of note with frontmatter."
    )
    (vault_path / "existing_note.md").write_text("This is the body.")

    (vault_path / "notes").mkdir()
    (vault_path / "notes" / "person.md").write_text(
        "---\n"
        "entity_id: '456'\n"
        "entity_type: person\n"
        "---\n"
        "About a person."
    )

    return ObsidianService(vault_path=str(vault_path))


class TestObsidianService:
    def test_build_cache(self, obsidian_service):
        cache = obsidian_service._build_cache()
        assert "note_with_frontmatter" in cache
        assert "existing_note" in cache
        assert "person" in cache
        assert "notes/person" in cache
        assert len(cache) == 4

    def test_resolve_link_simple(self, obsidian_service):
        result = obsidian_service.resolve_link("note_with_frontmatter")
        assert result['entity_name'] == "note_with_frontmatter"
        assert result['entity_id'] == "123"
        assert result['entity_type'] == "test"
        assert result['aliases'] == ["test_alias"]
        assert result['short_summary'] == "A test note."
        assert result['display_text'] == "note_with_frontmatter"
        assert os.path.exists(result['file_path'])

    def test_resolve_link_with_alias(self, obsidian_service):
        result = obsidian_service.resolve_link("note_with_frontmatter|aliased")
        assert result['entity_name'] == "note_with_frontmatter"
        assert result['display_text'] == "aliased"

    def test_resolve_link_with_path(self, obsidian_service):
        result = obsidian_service.resolve_link("notes/person")
        assert result['entity_name'] == "person"
        assert result['entity_long_name'] == "notes/person"
        assert result['entity_id'] == "456"
        assert result['entity_type'] == "person"
        assert os.path.exists(result['file_path'])

    def test_resolve_link_non_existent(self, obsidian_service):
        result = obsidian_service.resolve_link("non_existent_note")
        assert result['file_path'] is None
        assert result['entity_name'] == "non_existent_note"
        assert result['entity_id'] is None

    def test_update_link_add_frontmatter_to_existing(self, obsidian_service):
        metadata = {"entity_id": "new-id", "entity_type": "thing"}
        success = obsidian_service.update_link("existing_note", metadata)
        assert success

        file_path = obsidian_service.find_note_by_name("existing_note")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert content.startswith('---')
        assert "entity_id: new-id" in content
        assert "entity_type: thing" in content
        assert content.endswith("This is the body.")

    def test_update_link_modify_existing_frontmatter(self, obsidian_service):
        metadata = {"entity_id": "updated-id", "new_prop": "value", "short_summary": None}
        success = obsidian_service.update_link("note_with_frontmatter", metadata)
        assert success

        file_path = obsidian_service.find_note_by_name("note_with_frontmatter")
        frontmatter = obsidian_service._parse_yaml_frontmatter(file_path)

        assert frontmatter['entity_id'] == "updated-id"
        assert frontmatter['entity_type'] == "test"  # preserved
        assert frontmatter['aliases'] == ["test_alias"]  # preserved
        assert frontmatter['new_prop'] == "value"  # added
        assert 'short_summary' not in frontmatter  # removed

    def test_update_link_create_new_note(self, obsidian_service):
        metadata = {"entity_id": "a-new-id"}
        success = obsidian_service.update_link("completely_new_note", metadata)
        assert success

        file_path = obsidian_service.find_note_by_name("completely_new_note")
        assert file_path is not None
        assert os.path.exists(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "entity_id: a-new-id" in content

    def test_update_link_create_new_note_with_path(self, obsidian_service):
        link_text = "new_folder/another_new_note"
        metadata = {"entity_id": "another-id"}
        success = obsidian_service.update_link(link_text, metadata)
        assert success

        # Check cache is updated
        file_path = obsidian_service.find_note_by_name(link_text)
        assert file_path is not None
        assert os.path.exists(file_path)
        assert "new_folder" in file_path
        assert "another_new_note.md" in file_path

        # Check file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "entity_id: another-id" in content

    def test_get_cache_stats(self, obsidian_service):
        stats = obsidian_service.get_cache_stats()
        assert stats['total_notes'] == 4  # from fixture setup
        assert stats['vault_path'] == obsidian_service.vault_path
        assert stats['cache_built'] is True

    def test_find_note_by_name(self, obsidian_service):
        path = obsidian_service.find_note_by_name("person")
        assert path is not None
        assert path.endswith("person.md")

        path = obsidian_service.find_note_by_name("non_existent")
        assert path is None
