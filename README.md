
# NotionMail

## Summary

NotionMail is a mail application that uses the Notion API for email storage and retrieval, offering three operating modes:

1. **Basic Mode (`basic_functionality.py`)**: Core sending/reading messages via Notion API.
2. **Advanced Mode (`advanced.py`)**: Command-based interaction with search features.
3. **Chat Mode (`chat-mail.py`)**: Natural language interface for email interaction.

## Setup

### Minimal Requirements
- Python 3.9+
- `.env` file with:
NOTION_KEY=your_notion_integration_key
DATABASE_ID=your_notion_database_id
- Install dependencies: `pip install -r requirements.txt`

### Advanced Features (Optional)
- Additional keys for `.env`:
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=notion-mail

## Running NotionMail

### Basic Mode
python basic_functionality.py
Implements core functionality:
- Send messages from a specific sender to a recipient
- Read messages for a given recipient

### Advanced Mode
python advanced.py
Features:
- User session simulation (login/logout)
- Keyword search across messages
- Semantic search using embeddings

### Chat Mode
python chat-mail.py
- Natural language interface to email operations
- Converts user queries to structured commands

## Implementation Details

### Tool-Based Architecture
Rather than giving the model direct database access, the implementation defines specific primitives (read, send, search) that can be invoked. This approach:
- Restricts operations to pre-defined functions
- Establishes clear data access boundaries
- Enables processing large email volumes without performance degradation
- Allows extending functionality through additional primitives

## Future Improvements

### Security Enhancements
- Implement secure authentication
- Consider third-party auth services

### Feature Additions
- Message tagging and organization
- Read/unread tracking
- Multiple recipients with CC/BCC
- Conversation threading
- Additional search capabilities (date filtering, semantic queries)

## Development Notes
- Total time: 5 hours (4 hours implementation, 1 hour documentation)
- Testing: Manual verification with generated test data
- References: Notion API docs, OpenAI documentation, Pinecone documentation

The current implementation demonstrates both the minimal requirements and several enhancements that showcase what's possible when integrating modern AI capabilities with Notion as a database backend.