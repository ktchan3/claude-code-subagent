# Claude Code Subagent Experiments

This repository contains experiments with Claude Code's subagent capabilities and example implementations.

## Contents

### 🤖 Claude Code Agents (`.claude/agents/`)
Custom agent definitions for specialized development tasks:
- **api-architect** - API design and RESTful architecture
- **backend-architect** - Backend system design and implementation
- **database-architect** - Database schema design and optimization
- **frontend-architect** - Frontend UI/UX development
- **python-specialist** - Python-specific development expertise
- **technical-documentation-writer** - Comprehensive documentation creation

### 📦 Projects

#### People Management System (`people-management-system/`)
A complete client-server application demonstrating full-stack Python development:
- **Server**: FastAPI REST API with SQLite database
- **Client**: PySide6 desktop GUI application
- **Features**: CRUD operations, authentication, advanced search, statistics dashboard
- **Documentation**: Complete architecture, development, and deployment guides

[View People Management System README](people-management-system/README.md)

### 🧪 Examples
- **React Components** (`components/`) - Example UI components
- **Test Files** - Various test implementations and examples

## Using Claude Code Agents

The agents in this repository can be used with Claude Code to enhance development capabilities. Each agent specializes in specific areas:

1. **Load agents**: Use the `/agents` command in Claude Code
2. **Invoke agents**: Use the specialized agents for specific tasks
3. **Customize**: Modify agent definitions to suit your needs

## Getting Started

### People Management System
```bash
cd people-management-system
source activate.sh
make run-server  # Start the API server
make run-client  # Start the GUI client
```

### Agent Development
View and customize agent definitions in `.claude/agents/` to create your own specialized development assistants.

## Repository Structure
```
claude-code-subagent/
├── .claude/agents/          # Claude Code agent definitions
├── people-management-system/# Full-stack Python application
│   ├── server/             # FastAPI backend
│   ├── client/             # PySide6 GUI
│   ├── shared/             # Shared models and utilities
│   └── docs/               # Documentation
├── components/             # Example React components
└── test-file.js           # Example test file
```

## Technologies Used
- **Python 3.11+** with UV package manager
- **FastAPI** for REST API development
- **PySide6** for desktop GUI applications
- **SQLite** with SQLAlchemy ORM
- **Claude Code** for AI-assisted development

## License
This repository is for educational and experimental purposes.

---
🤖 Created with [Claude Code](https://claude.ai/code)