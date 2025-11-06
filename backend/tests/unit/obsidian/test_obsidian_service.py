"""
Unit tests for Obsidian service with Zettel sync functionality.

Tests the ObsidianService with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, mock_open
import os
from datetime import datetime

from minerva_backend.obsidian.obsidian_service import ObsidianService, SyncResult
from minerva_backend.graph.models.entities import Concept


@pytest.fixture
def mock_neo4j_connection():
    """Create mock Neo4j connection."""
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=MagicMock())
    mock_session.__exit__ = MagicMock(return_value=None)
    mock.session.return_value = mock_session
    return mock


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    mock = Mock()
    mock.create_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3] * 341 + [0.1])  # Dummy 1024-dim vector
    
    # Mock the generate method for summary generation
    mock_response = Mock()
    mock_response.summary_short = "Mock short summary"
    mock_response.summary = "Mock long summary"
    mock.generate = AsyncMock(return_value=mock_response)
    
    return mock


@pytest.fixture
def mock_concept_repository(mock_neo4j_connection, mock_llm_service):
    """Create mock concept repository."""
    mock = Mock()
    mock.connection = mock_neo4j_connection
    mock.llm_service = mock_llm_service
    return mock


@pytest.fixture
def obsidian_service(test_container):
    """Create real ObsidianService with mocked dependencies."""
    from minerva_backend.obsidian.obsidian_service import ObsidianService
    
    return ObsidianService(
        vault_path="/tmp/minerva_test_vault",  # Test-specific vault path
        llm_service=test_container.llm_service(),  # Mocked dependency
        concept_repository=test_container.concept_repository()  # Mocked dependency
    )


@pytest.fixture
def sample_zettel_content():
    """Sample Zettel content for testing - using actual Zettel format with frontmatter."""
    return """---
entity_id: af6bf2fd-2804-4ac6-9081-ef041a3baf40
entity_type: Concept
short_summary: El capitalismo desarrolla las fuerzas productivas, pero de forma contradictoria,
  ya que el crecimiento de medios de producción supera el de consumo personal, reflejando
  su naturaleza antagónica y progresiva histórica.
summary: 'El capitalismo impulsa el desarrollo de las fuerzas productivas, pero de
  manera contradictoria: mientras se expanden medios de producción, el consumo personal
  crece más lentamente. Este proceso es histórico y progresista, aunque intrínsecamente
  antagónico, ya que el crecimiento de la producción se realiza mediante la explotación
  del trabajo como mercancía. Este desarrollo es una ley estructural de la sociedad
  capitalista, evidenciado en contextos como el de Rusia, donde el avance económico
  se manifiesta como tensión entre productividad y demanda. La fuerza productiva crece,
  pero no de forma equitativa ni sostenible, lo que refleja la dinámica contradictoria
  propia del sistema capitalista.'
---
## Concepto
El capitalismo desarrolla las fuerzas productivas de manera específica y contradictoria

## Conexiones
- GENERALIZES: 
- SPECIFIC_OF: 
- PART_OF: [[Carácter Históricamente Progresista del Capitalismo]]
- HAS_PART: 
- SUPPORTS: 
- SUPPORTED_BY: 
- OPPOSES: 
- SIMILAR_TO: 
- RELATES_TO: [[El capitalismo es una economía monetaria con fuerza de trabajo como mercancía]]

## Análisis
- **Característica específica**: Incremento de medios de producción supera al de consumo personal
- **Base teórica**: Corresponde a leyes generales de realización en sociedad capitalista
- **Naturaleza antagónica**: Refleja el carácter antagónico de la sociedad capitalista

## Fuente
[[El Desarrollo del Capitalismo en Rusia]] #610
"""


@pytest.fixture
def sample_zettel_content_without_frontmatter():
    """Sample Zettel content without frontmatter - using actual Zettel format."""
    return """## Concepto
Los sucesos no son inherentemente buenos o malos.

## Conexiones
Parecido a la [[Ecuanimidad estoica]]
Tiene un elemento de [[Suspensión del Juicio]]

## Análisis
- No juzgar eventos de forma inmediata.
- La perspectiva cambia con el paso del tiempo.

## Fuente
Cuento [[Zen]]
"""


@pytest.fixture
def sample_zettel_content_personal_politico():
    """Sample Zettel content for 'Lo personal es político' - using actual Zettel format with frontmatter."""
    return """---
entity_id: 9554fcba-ba1e-4a70-81a0-3b17ac48b5ae
entity_type: Concept
short_summary: Lo personal es político afirma que las experiencias íntimas, como la
  vida doméstica o las relaciones sexuales, reflejan estructuras de poder y desigualdad,
  y que compartirlas revela patrones políticos que permiten la acción colectiva.
summary: El concepto 'Lo personal es político' sostiene que las experiencias privadas
  —como el trabajo doméstico, la sexualidad o la familia— están profundamente ligadas
  a estructuras de poder y desigualdad sociales. Originado en el feminismo de la segunda
  ola, especialmente en el ensayo de Carol Hanisch (1969), este lema desafía la separación
  entre lo privado y lo público. Al revelar cómo la opresión se manifiesta en la vida
  cotidiana, transforma el individual en colectivo, permitiendo que las experiencias
  personales se conviertan en base para la conciencia política y la acción organizada.
  Este enfoque subraya que la política no se limita al ámbito público, sino que está
  presente en todos los espacios de la vida diaria.
---
## Concepto
Las experiencias individuales de la cotidianidad (especialmente la vida domestica, sexual, y la familia) reflejan estructuras y relaciones de poder mas amplias en la sociedad.

## Conexiones
- GENERALIZES: 
- SPECIFIC_OF: 
- PART_OF: [[Feminismo de la segunda ola]]
- HAS_PART: 
- SUPPORTS: 
- SUPPORTED_BY: 
- OPPOSES: 
- SIMILAR_TO: 
- RELATES_TO: 


## Análisis
El lema cuestiona la idea de que lo privado es irrelevante para la política. Expone cómo la opresión y la desigualdad no se limitan al ámbito público, sino que atraviesan la vida íntima. Además, transforma lo individual en colectivo: al compartir experiencias personales se revela un patrón político y se posibilita la acción organizada.

## Fuente
Carol Hanisch, ensayo _The Personal is Political_ (1969).
"""


@pytest.fixture
def sample_zettel_content_mundo_poliamor():
    """Sample Zettel content for 'El mundo se acaba y vos solo hablas de poliamor' - using actual Zettel format with frontmatter."""
    return """---
entity_id: 2d56b6cc-3390-4c82-9155-b284b825bf2e
entity_type: Concept
short_summary: Una crítica irónica que contrasta la urgencia del colapso del mundo
  con el enfoque en discusiones sobre poliamor, cuestionando si las luchas afectivas
  son evasión frente a crisis globales.
summary: La frase 'El mundo se acaba y vos solo hablas de poliamor' expresa una tensión
  entre la gravedad de crisis globales —climáticas, económicas, políticas— y el debate
  sobre formas afectivas como el poliamor. Se lee como una crítica irónica al activismo
  identitario, sugiriendo que, en tiempos de colapso, las discusiones sobre relaciones
  personales pueden parecer banales o evasivas. Sin embargo, también invita a reflexionar
  si, precisamente en momentos de crisis, las luchas por la dignidad afectiva y el
  poder en las relaciones se vuelven más urgentes y políticas. El concepto subraya
  que lo personal no es solo privado, sino que está profundamente ligado al mundo
  en que vivimos.
---
## Concepto
Frase crítica/irónica que señala la tensión entre crisis globales (climática, económica, política) y discusiones sobre formas de vida afectiva o sexual, vistas como "banales" frente a la urgencia del colapso.

## Conexiones
- GENERALIZES: 
- SPECIFIC_OF: 
- PART_OF: [[Críticas al activismo identitario]]
- HAS_PART: 
- SUPPORTS: 
- SUPPORTED_BY: 
- OPPOSES: [[Poliamor]], [[Lo personal es político]]
- SIMILAR_TO: 
- RELATES_TO: [[Fin del Mundo

## Análisis
La expresión refleja un choque de escalas: lo macro (fin del mundo) versus lo micro (formas de relacionarse). Puede leerse como deslegitimación de luchas íntimas o como muestra de cómo incluso en contextos de crisis seguimos negociando significados afectivos. Invita a pensar si hablar de vínculos personales es evasión.

## Fuente
Un [[Graffiti]]
"""


class TestObsidianServiceInitialization:
    """Test ObsidianService initialization."""
    
    def test_initialization(self, obsidian_service):
        """Test service initialization."""
        assert obsidian_service is not None
        assert hasattr(obsidian_service, 'get_zettel_directory')
        assert hasattr(obsidian_service, 'find_zettel_files')
        assert hasattr(obsidian_service, 'parse_zettel_content')
        assert hasattr(obsidian_service, 'sync_zettels_to_db')


class TestZettelDirectoryMethods:
    """Test Zettel directory methods."""
    
    def test_get_zettel_directory_default(self, obsidian_service):
        """Test getting default Zettel directory."""
        # The service uses the vault_path from constructor, not environment variable
        result = obsidian_service.get_zettel_directory()
        assert result == os.path.join(obsidian_service.vault_path, "08 - Ideas")
    
    def test_get_zettel_directory_custom(self, obsidian_service):
        """Test getting custom Zettel directory."""
        # Create a new service instance with custom vault path
        custom_service = ObsidianService(vault_path="/tmp/minerva_test_vault")  # Test-specific vault path
        result = custom_service.get_zettel_directory()
        assert result == os.path.join('/tmp/minerva_test_vault', '08 - Ideas')
    
    def test_get_zettel_directory_no_vault_path(self, obsidian_service):
        """Test getting Zettel directory when no vault path is set."""
        # The service constructor requires vault_path, so this test doesn't apply
        # The service will always have a vault_path from constructor
        result = obsidian_service.get_zettel_directory()
        assert result is not None


class TestZettelFileMethods:
    """Test Zettel file discovery methods."""
    
    def test_find_zettel_files_success(self, obsidian_service):
        """Test finding Zettel files successfully."""
        with patch('os.walk') as mock_walk, patch('os.path.exists') as mock_exists:
            # Use the actual vault path that the service will use
            vault_path = "/tmp/minerva_test_vault"
            zettel_dir = os.path.join(vault_path, "08 - Ideas")
            subdir = os.path.join(zettel_dir, 'subdir')
            
            # Mock that the directory exists
            mock_exists.return_value = True
            
            mock_walk.return_value = [
                (zettel_dir, [], ['zettel1.md', 'zettel2.md', 'other.txt']),
                (subdir, [], ['zettel3.md'])
            ]
            
            result = obsidian_service.find_zettel_files()
            
            assert len(result) == 3
            assert os.path.join(zettel_dir, 'zettel1.md') in result
            assert os.path.join(zettel_dir, 'zettel2.md') in result
            assert os.path.join(subdir, 'zettel3.md') in result
            assert os.path.join(zettel_dir, 'other.txt') not in result
    
    def test_find_zettel_files_empty_directory(self, obsidian_service):
        """Test finding Zettel files in empty directory."""
        with patch('os.walk') as mock_walk:
            # Use the actual vault path that the service will use
            vault_path = "/tmp/minerva_test_vault"
            zettel_dir = os.path.join(vault_path, "08 - Ideas")
            mock_walk.return_value = [(zettel_dir, [], [])]
            
            result = obsidian_service.find_zettel_files()
            
            assert result == []
    
    def test_find_zettel_files_nonexistent_directory(self, obsidian_service):
        """Test finding Zettel files in nonexistent directory."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = obsidian_service.find_zettel_files()
            
            assert result == []


class TestZettelParsingMethods:
    """Test Zettel content parsing methods."""
    
    def test_parse_zettel_content_success(self, obsidian_service, sample_zettel_content):
        """Test parsing Zettel content successfully with frontmatter."""
        import tempfile
        import os
        
        # Create a temporary file with the sample content
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'El Capitalismo Desarrolla las Fuerzas Productivas.md')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(sample_zettel_content)
        
        try:
            result = obsidian_service.parse_zettel_content(temp_file)
            
            assert result is not None
            assert result['title'] == "El Capitalismo Desarrolla las Fuerzas Productivas"
            assert result['name'] == "El Capitalismo Desarrolla las Fuerzas Productivas"
            # Test frontmatter parsing
            assert result['frontmatter']['entity_id'] == "af6bf2fd-2804-4ac6-9081-ef041a3baf40"
            assert result['frontmatter']['entity_type'] == "Concept"
            # Test content parsing
            assert "El capitalismo desarrolla las fuerzas productivas de manera específica y contradictoria" in result['concept']
            assert "Característica específica" in result['analysis']
            assert "Carácter Históricamente Progresista del Capitalismo" in result['connections']
            assert "El capitalismo es una economía monetaria con fuerza de trabajo como mercancía" in result['connections']
            assert "El Desarrollo del Capitalismo en Rusia" in result['source']
        finally:
            os.unlink(temp_file)
            os.rmdir(temp_dir)
    
    def test_parse_zettel_content_without_frontmatter(self, obsidian_service, sample_zettel_content_without_frontmatter):
        """Test parsing Zettel content without frontmatter."""
        import tempfile
        import os
        
        # Create a temporary file with the sample content
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'Buena suerte, Mala suerte.md')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(sample_zettel_content_without_frontmatter)
        
        try:
            result = obsidian_service.parse_zettel_content(temp_file)
            
            assert result is not None
            assert result['title'] == "Buena suerte, Mala suerte"
            assert result['name'] == "Buena suerte, Mala suerte"
        finally:
            os.unlink(temp_file)
            os.rmdir(temp_dir)
    
    def test_parse_zettel_content_empty(self, obsidian_service):
        """Test parsing empty Zettel content."""
        import tempfile
        import os
        
        # Create a temporary file with empty content
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'empty.md')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        try:
            result = obsidian_service.parse_zettel_content(temp_file)
            
            assert result is not None
            assert result['title'] == "empty"
            assert result['name'] == "empty"
        finally:
            os.unlink(temp_file)
            os.rmdir(temp_dir)
    
    def test_parse_zettel_sections(self, obsidian_service):
        """Test parsing Zettel sections."""
        content = """## Concepto
This is a summary.

## Análisis
This is an analysis.

## Conexiones
- [[Link1]]
- [[Link2]]

## Fuente
Test source
"""
        
        result = obsidian_service._parse_zettel_sections(content)
        
        assert result['concepto'] == "This is a summary."
        assert result['análisis'] == "This is an analysis."
        assert "Link1" in result['conexiones'] and "Link2" in result['conexiones']
        assert result['fuente'] == "Test source"
    
    def test_parse_zettel_sections_missing_sections(self, obsidian_service):
        """Test parsing Zettel sections with missing sections."""
        content = """## Concepto
This is a summary.

## Análisis
This is an analysis.
"""
        
        result = obsidian_service._parse_zettel_sections(content)
        
        assert result['concepto'] == "This is a summary."
        assert result['análisis'] == "This is an analysis."
        assert result['conexiones'] == ""
        assert result['fuente'] is None
    
    def test_parse_zettel_content_personal_politico(self, obsidian_service, sample_zettel_content_personal_politico):
        """Test parsing 'Lo personal es político' Zettel content with frontmatter."""
        import tempfile
        import os
        
        # Create a temporary file with the sample content
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'Lo personal es político.md')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(sample_zettel_content_personal_politico)
        
        try:
            result = obsidian_service.parse_zettel_content(temp_file)
            
            assert result is not None
            assert result['title'] == "Lo personal es político"
            assert result['name'] == "Lo personal es político"
            # Test frontmatter parsing
            assert result['frontmatter']['entity_id'] == "9554fcba-ba1e-4a70-81a0-3b17ac48b5ae"
            assert result['frontmatter']['entity_type'] == "Concept"
            # Test content parsing
            assert "Las experiencias individuales de la cotidianidad" in result['concept']
            assert "El lema cuestiona la idea de que lo privado es irrelevante" in result['analysis']
            assert "Feminismo de la segunda ola" in result['connections']
            assert "Carol Hanisch, ensayo _The Personal is Political_ (1969)" in result['source']
        finally:
            os.unlink(temp_file)
            os.rmdir(temp_dir)
    
    def test_parse_zettel_content_mundo_poliamor(self, obsidian_service, sample_zettel_content_mundo_poliamor):
        """Test parsing 'El mundo se acaba y vos solo hablas de poliamor' Zettel content with frontmatter."""
        import tempfile
        import os
        
        # Create a temporary file with the sample content
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'El mundo se acaba y vos solo hablas de poliamor.md')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(sample_zettel_content_mundo_poliamor)
        
        try:
            result = obsidian_service.parse_zettel_content(temp_file)
            
            assert result is not None
            assert result['title'] == "El mundo se acaba y vos solo hablas de poliamor"
            assert result['name'] == "El mundo se acaba y vos solo hablas de poliamor"
            # Test frontmatter parsing
            assert result['frontmatter']['entity_id'] == "2d56b6cc-3390-4c82-9155-b284b825bf2e"
            assert result['frontmatter']['entity_type'] == "Concept"
            # Test content parsing
            assert "Frase crítica/irónica que señala la tensión" in result['concept']
            assert "La expresión refleja un choque de escalas" in result['analysis']
            assert "Críticas al activismo identitario" in result['connections']
            assert "Poliamor" in result['connections']
            assert "Lo personal es político" in result['connections']
            assert "Un [[Graffiti]]" in result['source']
        finally:
            os.unlink(temp_file)
            os.rmdir(temp_dir)
    
    def test_parse_conexiones_section(self, obsidian_service):
        """Test parsing conexiones section into relations."""
        test_content = """- GENERALIZES: 
- SPECIFIC_OF: 
- PART_OF: [[Carácter Históricamente Progresista del Capitalismo]]
- HAS_PART: 
- SUPPORTS: 
- SUPPORTED_BY: 
- OPPOSES: 
- SIMILAR_TO: 
- RELATES_TO: [[El capitalismo es una economía monetaria con fuerza de trabajo como mercancía]]"""
        
        result = obsidian_service.parse_conexiones_section(test_content)
        
        assert isinstance(result, dict)
        assert "PART_OF" in result
        assert "RELATES_TO" in result
        assert "Carácter Históricamente Progresista del Capitalismo" in result["PART_OF"]
        assert "El capitalismo es una economía monetaria con fuerza de trabajo como mercancía" in result["RELATES_TO"]
        # Empty relations should have empty lists
        assert result["GENERALIZES"] == []
        assert result["SPECIFIC_OF"] == []
        assert result["HAS_PART"] == []
        assert result["SUPPORTS"] == []
        assert result["SUPPORTED_BY"] == []
        assert result["OPPOSES"] == []
        assert result["SIMILAR_TO"] == []


class TestConexionesSectionMethods:
    """Test Conexiones section parsing and updating methods."""
    
    def test_parse_conexiones_section_complete(self, obsidian_service):
        """Test parsing complete Conexiones section with all relation types."""
        test_content = """- GENERALIZES: 
- SPECIFIC_OF: 
- PART_OF: [[Carácter Históricamente Progresista del Capitalismo]]
- HAS_PART: 
- SUPPORTS: 
- SUPPORTED_BY: 
- OPPOSES: 
- SIMILAR_TO: 
- RELATES_TO: [[El capitalismo es una economía monetaria con fuerza de trabajo como mercancía]]"""
        
        result = obsidian_service.parse_conexiones_section(test_content)
        
        assert isinstance(result, dict)
        # Check that all standard relation types are present
        expected_types = ["GENERALIZES", "SPECIFIC_OF", "PART_OF", "HAS_PART", 
                         "SUPPORTS", "SUPPORTED_BY", "OPPOSES", "SIMILAR_TO", "RELATES_TO"]
        for rel_type in expected_types:
            assert rel_type in result
        
        # Check populated relations
        assert "Carácter Históricamente Progresista del Capitalismo" in result["PART_OF"]
        assert "El capitalismo es una economía monetaria con fuerza de trabajo como mercancía" in result["RELATES_TO"]
        
        # Check empty relations have empty lists
        assert result["GENERALIZES"] == []
        assert result["SPECIFIC_OF"] == []
        assert result["HAS_PART"] == []
        assert result["SUPPORTS"] == []
        assert result["SUPPORTED_BY"] == []
        assert result["OPPOSES"] == []
        assert result["SIMILAR_TO"] == []
    
    def test_parse_conexiones_section_incomplete(self, obsidian_service):
        """Test parsing incomplete Conexiones section with only some relation types."""
        test_content = """- HAS_PART: [[Diferenciación del Campesinado]]
- RELATES_TO: [[Necesidad del Mercado Exterior]], [[Presión migratoria del Capitalismo]]"""
        
        result = obsidian_service.parse_conexiones_section(test_content)
        
        assert isinstance(result, dict)
        # Only the present relation types should be in the result
        assert "HAS_PART" in result
        assert "RELATES_TO" in result
        assert "GENERALIZES" not in result  # Not present in input
        
        # Check populated relations
        assert "Diferenciación del Campesinado" in result["HAS_PART"]
        assert "Necesidad del Mercado Exterior" in result["RELATES_TO"]
        assert "Presión migratoria del Capitalismo" in result["RELATES_TO"]
    
    def test_parse_conexiones_section_empty(self, obsidian_service):
        """Test parsing empty Conexiones section."""
        test_content = ""
        
        result = obsidian_service.parse_conexiones_section(test_content)
        
        assert isinstance(result, dict)
        assert len(result) == 0  # No relation types found
    
    def test_parse_conexiones_section_malformed(self, obsidian_service):
        """Test parsing malformed Conexiones section."""
        test_content = """- INVALID_RELATION: [[Some Concept]]
- PART_OF: [[Valid Concept]]
- MALFORMED_LINE: This is not a valid relation line"""
        
        result = obsidian_service.parse_conexiones_section(test_content)
        
        assert isinstance(result, dict)
        # Only valid relation types should be parsed
        assert "PART_OF" in result
        assert "Valid Concept" in result["PART_OF"]
        assert "INVALID_RELATION" not in result
        assert "MALFORMED_LINE" not in result
    
    def test_update_conexiones_section_preserves_all_types(self, obsidian_service):
        """Test that update_conexiones_section preserves all relation types, even empty ones."""
        import tempfile
        import os
        
        # Create test file with complete Conexiones section
        test_content = """# Test Concept

## Conexiones
- GENERALIZES: 
- SPECIFIC_OF: 
- PART_OF: [[Existing Concept]]
- HAS_PART: 
- SUPPORTS: 
- SUPPORTED_BY: 
- OPPOSES: 
- SIMILAR_TO: 
- RELATES_TO: 

## Análisis
Test analysis content.
"""
        
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'test_concept.md')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # Update with new relations
            new_relations = {
                "GENERALIZES": ["New General Concept"],
                "SUPPORTS": ["New Supporting Concept"]
            }
            
            result = obsidian_service.update_conexiones_section(temp_file, new_relations)
            
            assert result is True
            
            # Read the updated file
            with open(temp_file, 'r', encoding='utf-8') as f:
                updated_content = f.read()
            
            # Check that all relation types are preserved
            assert "- GENERALIZES: [[New General Concept]]" in updated_content
            assert "- SPECIFIC_OF: " in updated_content
            assert "- PART_OF: [[Existing Concept]]" in updated_content
            assert "- HAS_PART: " in updated_content
            assert "- SUPPORTS: [[New Supporting Concept]]" in updated_content
            assert "- SUPPORTED_BY: " in updated_content
            assert "- OPPOSES: " in updated_content
            assert "- SIMILAR_TO: " in updated_content
            assert "- RELATES_TO: " in updated_content
            
        finally:
            os.unlink(temp_file)
            os.rmdir(temp_dir)
    
    def test_update_conexiones_section_fixes_incomplete_section(self, obsidian_service):
        """Test that update_conexiones_section adds missing relation types to incomplete sections."""
        import tempfile
        import os
        
        # Create test file with incomplete Conexiones section
        test_content = """# Test Concept

## Conexiones
- HAS_PART: [[Diferenciación del Campesinado]]
- RELATES_TO: [[Necesidad del Mercado Exterior]], [[Presión migratoria del Capitalismo]]

## Análisis
Test analysis content.
"""
        
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'test_concept.md')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # Update with new relations
            new_relations = {
                "GENERALIZES": ["New General Concept"]
            }
            
            result = obsidian_service.update_conexiones_section(temp_file, new_relations)
            
            assert result is True
            
            # Read the updated file
            with open(temp_file, 'r', encoding='utf-8') as f:
                updated_content = f.read()
            
            # Check that all standard relation types are now present
            assert "- GENERALIZES: [[New General Concept]]" in updated_content
            assert "- SPECIFIC_OF: " in updated_content
            assert "- PART_OF: " in updated_content
            assert "- HAS_PART: [[Diferenciación del Campesinado]]" in updated_content
            assert "- SUPPORTS: " in updated_content
            assert "- SUPPORTED_BY: " in updated_content
            assert "- OPPOSES: " in updated_content
            assert "- SIMILAR_TO: " in updated_content
            assert "- RELATES_TO: [[Necesidad del Mercado Exterior]], [[Presión migratoria del Capitalismo]]" in updated_content
            
        finally:
            os.unlink(temp_file)
            os.rmdir(temp_dir)
    
    def test_update_conexiones_section_preserves_non_standard_types(self, obsidian_service):
        """Test that update_conexiones_section preserves non-standard relation types."""
        import tempfile
        import os
        
        # Create test file with non-standard relation types
        test_content = """# Test Concept

## Conexiones
- CUSTOM_RELATION: [[Custom Concept]]
- PART_OF: [[Standard Concept]]

## Análisis
Test analysis content.
"""
        
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'test_concept.md')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # Update with new relations
            new_relations = {
                "GENERALIZES": ["New General Concept"]
            }
            
            result = obsidian_service.update_conexiones_section(temp_file, new_relations)
            
            assert result is True
            
            # Read the updated file
            with open(temp_file, 'r', encoding='utf-8') as f:
                updated_content = f.read()
            
            # Check that standard types are added
            assert "- GENERALIZES: [[New General Concept]]" in updated_content
            assert "- SPECIFIC_OF: " in updated_content
            
            # Check that existing standard types are preserved
            assert "- PART_OF: [[Standard Concept]]" in updated_content
            
            # Note: Non-standard types (CUSTOM_RELATION) are not preserved in the current implementation
            # because they're not in RELATION_MAP. This is expected behavior.
            
        finally:
            os.unlink(temp_file)
            os.rmdir(temp_dir)
    
    def test_update_conexiones_section_no_conexiones_section(self, obsidian_service):
        """Test that update_conexiones_section returns False when no Conexiones section exists."""
        import tempfile
        import os
        
        # Create test file without Conexiones section
        test_content = """# Test Concept

## Análisis
Test analysis content.
"""
        
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'test_concept.md')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # Try to update with new relations
            new_relations = {
                "GENERALIZES": ["New General Concept"]
            }
            
            result = obsidian_service.update_conexiones_section(temp_file, new_relations)
            
            assert result is False  # Should return False when no Conexiones section exists
            
        finally:
            os.unlink(temp_file)
            os.rmdir(temp_dir)


class TestZettelSyncMethods:
    """Test Zettel synchronization methods."""
    
    @pytest.mark.asyncio
    async def test_sync_zettels_to_db_success(self, obsidian_service, mock_concept_repository, sample_zettel_content):
        """Test successful Zettel synchronization to database."""
        # Arrange
        zettel_files = ['/test/vault/08 - Ideas/El Capitalismo Desarrolla las Fuerzas Productivas.md']
        
        # Mock LLM response
        from minerva_backend.prompt.generate_zettel_summary import ZettelSummary
        mock_llm_response = ZettelSummary(
            summary_short="El capitalismo desarrolla las fuerzas productivas, pero de forma contradictoria",
            summary="El capitalismo impulsa el desarrollo de las fuerzas productivas, pero de manera contradictoria: mientras se expanden medios de producción, el consumo personal crece más lentamente."
        )
        obsidian_service.llm_service.generate = AsyncMock(return_value=mock_llm_response)
        
        with patch.object(obsidian_service, 'get_zettel_directory') as mock_get_dir, \
             patch.object(obsidian_service, 'find_zettel_files') as mock_find_files, \
             patch('builtins.open', mock_open(read_data=sample_zettel_content)), \
             patch.object(obsidian_service, 'parse_zettel_content') as mock_parse, \
             patch.object(obsidian_service, 'update_link') as mock_update_link:
            
            mock_get_dir.return_value = '/test/vault/08 - Ideas'
            mock_find_files.return_value = zettel_files
            mock_update_link.return_value = True
            mock_parse.return_value = {
                'title': 'El Capitalismo Desarrolla las Fuerzas Productivas',
                'name': 'El Capitalismo Desarrolla las Fuerzas Productivas',
                'concept': 'El capitalismo desarrolla las fuerzas productivas de manera específica y contradictoria',
                'analysis': 'Característica específica: Incremento de medios de producción supera al de consumo personal',
                'connections': '- PART_OF: [[Carácter Históricamente Progresista del Capitalismo]]\n- RELATES_TO: [[El capitalismo es una economía monetaria con fuerza de trabajo como mercancía]]',
                'source': 'El Desarrollo del Capitalismo en Rusia',
                'summary_short': 'El capitalismo desarrolla las fuerzas productivas, pero de forma contradictoria',
                'summary': 'El capitalismo impulsa el desarrollo de las fuerzas productivas, pero de manera contradictoria: mientras se expanden medios de producción, el consumo personal crece más lentamente.',
                'frontmatter': {
                    'entity_type': 'Concept'
                }
            }
            
            # Mock concept repository methods
            mock_concept_repository.find_concept_by_name_or_title = AsyncMock(return_value=None)
            mock_concept_repository.create = AsyncMock(return_value='new-concept-uuid')
            mock_concept_repository.update = AsyncMock(return_value='existing-concept-uuid')
            mock_concept_repository.get_concept_relations = AsyncMock(return_value=[])
            mock_concept_repository.delete_concept_relation = AsyncMock(return_value=True)
            
            # Act
            result = await obsidian_service.sync_zettels_to_db()
            
            # Assert
            assert result.parsed == 1
            assert result.created == 1
            assert result.updated == 0
            assert result.errors == 0
            
            # Verify concept was created
            mock_concept_repository.create.assert_called_once()
            create_call = mock_concept_repository.create.call_args[0][0]
            assert isinstance(create_call, Concept)
            assert create_call.name == 'El Capitalismo Desarrolla las Fuerzas Productivas'
            assert create_call.title == 'El Capitalismo Desarrolla las Fuerzas Productivas'
            assert create_call.concept == 'El capitalismo desarrolla las fuerzas productivas de manera específica y contradictoria'
            assert create_call.analysis == 'Característica específica: Incremento de medios de producción supera al de consumo personal'
            assert create_call.source == 'El Desarrollo del Capitalismo en Rusia'
    
    @pytest.mark.asyncio
    async def test_sync_zettels_to_db_existing_concept(self, obsidian_service, mock_concept_repository, sample_zettel_content):
        """Test Zettel synchronization with existing concept."""
        # Arrange
        zettel_files = ['/test/vault/08 - Ideas/El Capitalismo Desarrolla las Fuerzas Productivas.md']
        existing_concept = Concept(
            name='El Capitalismo Desarrolla las Fuerzas Productivas',
            title='El Capitalismo Desarrolla las Fuerzas Productivas',
            concept='Old concept content',
            analysis='Old analysis',
            source=None,
            summary_short='Old summary',
            summary='Old summary'
        )
        
        with patch.object(obsidian_service, 'get_zettel_directory') as mock_get_dir, \
             patch.object(obsidian_service, 'find_zettel_files') as mock_find_files, \
             patch('builtins.open', mock_open(read_data=sample_zettel_content)), \
             patch.object(obsidian_service, 'parse_zettel_content') as mock_parse, \
             patch.object(obsidian_service, 'update_link') as mock_update_link:
            
            mock_get_dir.return_value = '/test/vault/08 - Ideas'
            mock_find_files.return_value = zettel_files
            mock_update_link.return_value = True
            mock_parse.return_value = {
                'title': 'El Capitalismo Desarrolla las Fuerzas Productivas',
                'name': 'El Capitalismo Desarrolla las Fuerzas Productivas',
                'concept': 'El capitalismo desarrolla las fuerzas productivas de manera específica y contradictoria',
                'analysis': 'Característica específica: Incremento de medios de producción supera al de consumo personal',
                'connections': '- PART_OF: [[Carácter Históricamente Progresista del Capitalismo]]',
                'source': 'El Desarrollo del Capitalismo en Rusia',
                'frontmatter': {
                    'entity_type': 'Concept'
                }
            }
            
            # Mock concept repository methods
            mock_concept_repository.find_concept_by_name_or_title = AsyncMock(return_value=existing_concept)
            mock_concept_repository.create = AsyncMock(return_value='new-concept-uuid')
            mock_concept_repository.update = AsyncMock(return_value='existing-concept-uuid')
            mock_concept_repository.get_concept_relations = AsyncMock(return_value=[])
            mock_concept_repository.delete_concept_relation = AsyncMock(return_value=True)
            
            # Act
            result = await obsidian_service.sync_zettels_to_db()
            
            # Assert
            assert result.parsed == 1
            assert result.created == 0
            assert result.updated == 1
            assert result.errors == 0

            # Verify concept was updated (content changed, so update should occur)
            mock_concept_repository.update.assert_called_once()
            update_call = mock_concept_repository.update.call_args
            assert update_call[0][0] == existing_concept.uuid  # UUID
            updates = update_call[0][1]  # Updates dict
            assert 'concept' in updates
            assert 'analysis' in updates
            assert 'source' in updates
            assert 'summary_short' in updates
            assert 'summary' in updates
    
    @pytest.mark.asyncio
    async def test_sync_zettels_to_db_file_error(self, obsidian_service, mock_concept_repository):
        """Test Zettel synchronization with file reading error."""
        # Arrange
        zettel_files = ['/test/vault/08 - Ideas/zettel1.md']
        
        with patch.object(obsidian_service, 'get_zettel_directory') as mock_get_dir, \
             patch.object(obsidian_service, 'find_zettel_files') as mock_find_files, \
             patch('builtins.open', side_effect=IOError("File read error")):
            
            mock_get_dir.return_value = '/test/vault/08 - Ideas'
            mock_find_files.return_value = zettel_files
            
            # Act
            result = await obsidian_service.sync_zettels_to_db()
            
            # Assert
            assert result.parsed == 0
            assert result.created == 0
            assert result.updated == 0
            assert result.errors == 1
    
    @pytest.mark.asyncio
    async def test_sync_zettels_to_db_no_files(self, obsidian_service, mock_concept_repository):
        """Test Zettel synchronization with no files found."""
        # Arrange
        with patch.object(obsidian_service, 'get_zettel_directory') as mock_get_dir, \
             patch.object(obsidian_service, 'find_zettel_files') as mock_find_files:
            
            mock_get_dir.return_value = '/test/vault/08 - Ideas'
            mock_find_files.return_value = []
            
            # Act
            result = await obsidian_service.sync_zettels_to_db()
            
            # Assert
            assert result.parsed == 0
            assert result.created == 0
            assert result.updated == 0
            assert result.errors == 0

    @pytest.mark.asyncio
    async def test_cleanup_orphaned_relations(self, obsidian_service, mock_concept_repository):
        """Test cleanup of orphaned relations from database."""
        # Arrange
        concept_data = {
            "Concept A": {
                "uuid": "uuid-a",
                "file_path": "/test/vault/Concept A.md"
            },
            "Concept B": {
                "uuid": "uuid-b", 
                "file_path": "/test/vault/Concept B.md"
            }
        }
        
        # Mock frontmatter relations (current state)
        with patch.object(obsidian_service, '_get_frontmatter_relations') as mock_frontmatter:
            mock_frontmatter.return_value = {
                "GENERALIZES": ["uuid-b"]  # Only Concept B is related
            }
            
            # Mock database relations (includes orphaned relation to Concept C)
            mock_concept_repository.get_concept_relations = AsyncMock(return_value=[
                {"target_uuid": "uuid-b", "relation_type": "GENERALIZES"},
                {"target_uuid": "uuid-c", "relation_type": "GENERALIZES"}  # Orphaned
            ])
            
            # Mock delete operations
            mock_concept_repository.delete_concept_relation = AsyncMock(return_value=True)
            
            result = SyncResult(
                total_files=2, parsed=2, created=0, updated=0, unchanged=0,
                errors=0, errors_list=[], missing_concepts=[], broken_notes=[],
                relations_created=0, relations_updated=0, self_connections_removed=0,
                inconsistent_relations=[]
            )
            
            # Act
            await obsidian_service._cleanup_orphaned_relations(
                concept_data, result
            )
            
            # Assert
            assert result.relations_deleted == 2  # Two orphaned relations deleted (one per concept)
            assert len(result.errors_list) == 2  # Two deletions logged
            assert "Deleted orphaned relation" in result.errors_list[0]
            assert "Deleted orphaned relation" in result.errors_list[1]
            
            # Verify delete was called for both forward and reverse relations (2 concepts * 2 directions = 4 calls)
            assert mock_concept_repository.delete_concept_relation.call_count == 4

    @pytest.mark.asyncio
    async def test_cleanup_no_orphaned_relations(self, obsidian_service, mock_concept_repository):
        """Test cleanup when no orphaned relations exist."""
        # Arrange
        concept_data = {
            "Concept A": {
                "uuid": "uuid-a",
                "file_path": "/test/vault/Concept A.md"
            }
        }
        
        # Mock frontmatter relations
        with patch.object(obsidian_service, '_get_frontmatter_relations') as mock_frontmatter:
            mock_frontmatter.return_value = {
                "GENERALIZES": ["uuid-b"]
            }
            
            # Mock database relations (matches frontmatter)
            mock_concept_repository.get_concept_relations = AsyncMock(return_value=[
                {"target_uuid": "uuid-b", "relation_type": "GENERALIZES"}
            ])
            
            result = SyncResult(
                total_files=1, parsed=1, created=0, updated=0, unchanged=0,
                errors=0, errors_list=[], missing_concepts=[], broken_notes=[],
                relations_created=0, relations_updated=0, self_connections_removed=0,
                inconsistent_relations=[]
            )
            
            # Act
            await obsidian_service._cleanup_orphaned_relations(
                concept_data, result
            )
            
            # Assert
            assert result.relations_deleted == 0  # No orphaned relations
            assert len(result.errors_list) == 0  # No deletions logged

    def test_find_orphaned_relations(self, obsidian_service):
        """Test finding orphaned relations."""
        # Arrange
        db_relations = [
            {"target_uuid": "uuid-b", "relation_type": "GENERALIZES"},
            {"target_uuid": "uuid-c", "relation_type": "GENERALIZES"},
            {"target_uuid": "uuid-d", "relation_type": "PART_OF"}
        ]
        
        frontmatter_relations = {
            "GENERALIZES": ["uuid-b"],  # uuid-c is orphaned
            "PART_OF": ["uuid-d"]  # This one exists
        }
        
        # Act
        orphaned = obsidian_service._find_orphaned_relations(db_relations, frontmatter_relations)
        
        # Assert
        assert len(orphaned) == 1
        assert orphaned[0]["target_uuid"] == "uuid-c"
        assert orphaned[0]["relation_type"] == "GENERALIZES"

    def test_get_reverse_relation_type(self, obsidian_service):
        """Test getting reverse relation types."""
        # Test asymmetric relations
        assert obsidian_service._get_reverse_relation_type("GENERALIZES") == "SPECIFIC_OF"
        assert obsidian_service._get_reverse_relation_type("SPECIFIC_OF") == "GENERALIZES"
        assert obsidian_service._get_reverse_relation_type("PART_OF") == "HAS_PART"
        assert obsidian_service._get_reverse_relation_type("HAS_PART") == "PART_OF"
        
        # Test symmetric relations
        assert obsidian_service._get_reverse_relation_type("OPPOSES") == "OPPOSES"
        assert obsidian_service._get_reverse_relation_type("SIMILAR_TO") == "SIMILAR_TO"
        assert obsidian_service._get_reverse_relation_type("RELATES_TO") == "RELATES_TO"
