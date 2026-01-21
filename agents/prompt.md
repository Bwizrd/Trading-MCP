# Ralph Agent Instructions - Trading Optimizer MCP Server

## Your Task

1. Read prd.json to see all user stories
2. Read progress.txt for patterns and history
3. Pick highest priority story where passes is false
4. Implement ONE story completely
5. Test the implementation
6. Git commit: feat(TM-XXX): Story title
7. Update prd.json marking passes true
8. APPEND learnings to progress.txt

## Context

Trading MCP Server for optimizing SL/TP parameters using:
- GET http://localhost:8000/deals/{date} - closed positions
- GET http://localhost:8020/getTickDataFromDB - tick data

Follow patterns in mcp_servers/ directory. Use async/await for API calls.
