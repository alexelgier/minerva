# Common Use Cases

Real-world scenarios and examples for using Minerva.

## Use Case 1: Daily Journaling Workflow

### Scenario
You write daily journal entries and want to extract insights automatically.

### Solution

1. **Write Journal** in Obsidian daily note
2. **Submit to Backend**:
   ```bash
   curl -X POST http://localhost:8000/api/journal/submit \
     -H "Content-Type: application/json" \
     -d '{"text": "Your journal text..."}'
   ```
3. **Review Entities**:
   - Open curation interface
   - Review extracted people, events, emotions
   - Approve or modify
4. **Review Relationships**:
   - Check extracted relationships
   - Approve connections
5. **Query Knowledge Graph**:
   - Find patterns over time
   - Discover connections
   - Analyze trends

### Benefits
- Automatic entity extraction
- Relationship discovery
- Pattern recognition
- Historical analysis

## Use Case 2: Book Reading and Note-Taking

### Scenario
You read books and take notes with quotes, want to extract concepts.

### Solution

1. **Create Book Notes**:
   ```markdown
   # Citas
   
   ## Chapter 1
   
   Important quote here
   
   123
   ```

2. **Parse Quotes**:
   ```python
   result = await quote_parse_graph.ainvoke({
       "file_path": "/path/to/book.md",
       "author": "Author Name",
       "title": "Book Title"
   })
   ```

3. **Extract Concepts**:
   ```python
   await concept_extraction_graph.ainvoke({
       "content_uuid": result["content_uuid"]
   })
   ```

4. **Review Concepts**:
   - Check concept proposals
   - Verify quote attributions
   - Accept or modify

5. **Link to Knowledge**:
   - Link concepts to journal entries
   - Connect to related entities
   - Build concept network

### Benefits
- Systematic concept extraction
- Atomic knowledge building
- Reusable concepts
- Knowledge network

## Use Case 3: Vault Organization

### Scenario
Your Obsidian inbox is cluttered, need help organizing.

### Solution

1. **Open minerva-desktop**
2. **Connect to minerva_agent**
3. **Ask Agent**:
   ```
   "Help me organize my inbox"
   ```
4. **Review Plan**:
   - Agent shows planned steps
   - Review file operations
5. **Execute**:
   - Agent moves files
   - Creates structure
   - Organizes content
6. **Verify**:
   - Check file changes
   - Approve organization
   - Commit changes

### Benefits
- Automated organization
- Consistent structure
- Time saving
- Agent assistance

## Use Case 4: Research Project

### Scenario
Researching a topic using multiple sources, want to build knowledge.

### Solution

1. **Collect Sources**:
   - Books, articles, notes
   - Store in Obsidian

2. **Process Quotes**:
   - Extract quotes from each source
   - Process with zettel
   - Extract concepts

3. **Write Analysis**:
   - Create analysis note
   - Link to concepts
   - Reference sources

4. **Process Analysis**:
   - Submit to backend
   - Extract entities
   - Link to concepts

5. **Build Knowledge**:
   - Query knowledge graph
   - Find connections
   - Discover insights
   - Visualize relationships

### Benefits
- Systematic research
- Concept extraction
- Knowledge building
- Connection discovery

## Use Case 5: Personal Knowledge Management

### Scenario
Build a personal knowledge base from journals, books, and notes.

### Solution

1. **Daily Journals**:
   - Write daily entries
   - Process with backend
   - Extract entities

2. **Book Reading**:
   - Take notes with quotes
   - Process with zettel
   - Extract concepts

3. **Note Taking**:
   - Create notes in Obsidian
   - Organize with agent
   - Link to knowledge graph

4. **Knowledge Building**:
   - Query knowledge graph
   - Find connections
   - Discover patterns
   - Build insights

### Benefits
- Comprehensive knowledge base
- Cross-referenced information
- Pattern discovery
- Personal insights

## Use Case 6: Concept Exploration

### Scenario
Explore a concept across journals, books, and notes.

### Solution

1. **Query Knowledge Graph**:
   ```cypher
   MATCH (c:Concept {name: "Concept Name"})
   RETURN c
   ```

2. **Find Related**:
   - Journal entries mentioning concept
   - Books with related quotes
   - Notes about concept

3. **Explore Connections**:
   - Related concepts
   - Linked entities
   - Temporal patterns

4. **Build Understanding**:
   - Review all sources
   - Synthesize information
   - Create analysis

### Benefits
- Comprehensive exploration
- Connection discovery
- Pattern recognition
- Deep understanding

## Use Case 7: Automated Note Processing

### Scenario
Automatically process notes from inbox, extract information.

### Solution

1. **Agent Processing**:
   - Agent reads inbox files
   - Analyzes content
   - Suggests organization

2. **Backend Processing**:
   - Submit notes to backend
   - Extract entities
   - Create relationships

3. **Concept Extraction**:
   - Process with zettel if quotes present
   - Extract concepts
   - Link to knowledge

4. **Organization**:
   - Agent organizes files
   - Creates structure
   - Links to knowledge graph

### Benefits
- Automated processing
- Consistent extraction
- Knowledge integration
- Time saving

## Tips for Success

### Start Simple
- Begin with one component
- Master basic workflows
- Gradually add complexity

### Be Consistent
- Regular journaling
- Systematic note-taking
- Consistent processing

### Review Regularly
- Review extracted entities
- Verify relationships
- Check concept quality

### Iterate
- Refine workflows
- Adjust processes
- Improve over time

## Related Documentation

- [Usage Overview](overview.md)
- [Integration Workflows](integration-workflows.md)
- [Component Usage Guides](minerva-desktop.md)

