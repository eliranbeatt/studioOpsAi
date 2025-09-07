# Trello MCP Server

This is a Model Context Protocol (MCP) server that provides Trello integration for the StudioOps AI Agent.

## Features

- Create Trello boards
- Create cards in boards
- Manage lists (create if they don't exist)
- Export project tasks to Trello boards
- Get user boards and board lists
- Add labels to cards

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Get Trello API credentials:
   - Go to https://trello.com/app-key to get your API key
   - Visit the authorization URL to get your token (replace YOUR_API_KEY with your actual key):
     ```
     https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&name=StudioOps&key=YOUR_API_KEY
     ```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

## Usage

Run the MCP server:
```bash
python server.py
```

## Available Tools

### create_board
Create a new Trello board.

**Parameters:**
- `name` (required): Board name
- `description` (optional): Board description
- `visibility` (optional): "private", "public", or "org" (default: "private")

### create_card
Create a card in a Trello board.

**Parameters:**
- `board_id` (required): Board ID where to create the card
- `list_name` (required): List name (will be created if doesn't exist)
- `name` (required): Card name
- `description` (optional): Card description
- `due_date` (optional): Due date in ISO format
- `labels` (optional): Array of label names

### get_boards
Get user's Trello boards.

**Parameters:**
- `filter` (optional): "all", "open", or "closed" (default: "open")

### get_board_lists
Get lists from a Trello board.

**Parameters:**
- `board_id` (required): Board ID

### export_project_tasks
Export project tasks to a Trello board.

**Parameters:**
- `project_id` (required): Project ID from database
- `board_name` (optional): Name for the new Trello board
- `project_data` (optional): Project data including plan items

## Integration with StudioOps

This MCP server integrates with the main StudioOps API to export project tasks to Trello boards. When a project is created and has a plan, the tasks can be automatically exported to a new Trello board for project management.

## Error Handling

The server includes comprehensive error handling for:
- Missing API credentials
- Trello API failures
- Network connectivity issues
- Invalid parameters

All errors are returned with descriptive messages to help with troubleshooting.