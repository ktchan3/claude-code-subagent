# Global Subagents Setup Guide for Claude Code

## Table of Contents
- [Overview](#overview)
- [Understanding Subagent Scopes](#understanding-subagent-scopes)
- [Directory Structure](#directory-structure)
- [Migration Guide](#migration-guide)
- [Verification and Testing](#verification-and-testing)
- [Best Practices](#best-practices)
- [When to Use Local vs Global](#when-to-use-local-vs-global)
- [Troubleshooting](#troubleshooting)
- [Available Global Subagents](#available-global-subagents)
- [Benefits of Global Subagents](#benefits-of-global-subagents)

## Overview

Claude Code supports two types of subagent configurations:
- **Local Subagents**: Project-specific agents stored within individual projects
- **Global Subagents**: User-wide agents available across all projects on your system

This guide documents the process of setting up global subagents, migrating from local to global configurations, and best practices for managing your subagent ecosystem.

## Understanding Subagent Scopes

### Local Subagents
- **Location**: `.claude/agents/` within your project directory
- **Scope**: Only available within the specific project
- **Use Case**: Project-specific customizations and specialized workflows
- **Priority**: Takes precedence over global agents when both exist

### Global Subagents
- **Location**: `~/.claude/agents/` in your home directory
- **Scope**: Available across all projects on your system
- **Use Case**: Common development patterns and standard workflows
- **Priority**: Used when no local agent with the same name exists

## Directory Structure

```
Home Directory (~/)
├── .claude/
│   └── agents/
│       ├── api-developer.md
│       ├── backend-developer.md
│       ├── code-debugger.md
│       ├── code-documenter.md
│       ├── code-refactor.md
│       ├── code-reviewer.md
│       ├── code-security-auditor.md
│       ├── code-standards-enforcer.md
│       ├── database-designer.md
│       ├── frontend-developer.md
│       ├── ios-developer.md
│       ├── javascript-developer.md
│       ├── mobile-developer.md
│       ├── php-developer.md
│       ├── python-developer.md
│       ├── typescript-developer.md
│       └── wordpress-developer.md

Project Directory
├── .claude/
│   └── agents/
│       └── [project-specific agents if any]
```

## Migration Guide

### Step 1: Check for Existing Global Directory

First, verify if the global agents directory already exists:

```bash
# Check if global directory exists
test -d ~/.claude/agents && echo "Directory exists" || echo "Directory does not exist"
```

### Step 2: Create Global Directory Structure

If the directory doesn't exist, create it:

```bash
# Create the global agents directory
mkdir -p ~/.claude/agents
```

The `-p` flag ensures parent directories are created if they don't exist and prevents errors if the directory already exists.

### Step 3: Copy Local Agents to Global Location

Copy all your local subagent files to the global directory:

```bash
# Copy all .md files from local to global with verbose output
cp -v .claude/agents/*.md ~/.claude/agents/

# Example output:
# '.claude/agents/api-developer.md' -> '/home/username/.claude/agents/api-developer.md'
# '.claude/agents/backend-developer.md' -> '/home/username/.claude/agents/backend-developer.md'
# ... (for all 17 agents)
```

### Step 4: Verify Migration Success

Verify that all agents were successfully copied:

```bash
# List all global agents
ls -la ~/.claude/agents/

# Count the number of agents
ls ~/.claude/agents/*.md | wc -l

# Verify specific agents exist
for agent in api-developer backend-developer code-debugger code-documenter; do
    test -f ~/.claude/agents/$agent.md && echo "✓ $agent.md exists" || echo "✗ $agent.md missing"
done
```

### Step 5: Optional - Remove Local Duplicates

After confirming the global setup works, you may want to remove local duplicates:

```bash
# Backup local agents first (recommended)
tar -czf local-agents-backup.tar.gz .claude/agents/

# Remove local agents that now exist globally
for agent in ~/.claude/agents/*.md; do
    local_agent=".claude/agents/$(basename $agent)"
    if [ -f "$local_agent" ]; then
        echo "Removing local duplicate: $local_agent"
        rm "$local_agent"
    fi
done
```

## Verification and Testing

### Quick Verification Script

Create and run this verification script to ensure all agents are properly installed:

```bash
#!/bin/bash
# verify-global-agents.sh

EXPECTED_AGENTS=(
    "api-developer"
    "backend-developer"
    "code-debugger"
    "code-documenter"
    "code-refactor"
    "code-reviewer"
    "code-security-auditor"
    "code-standards-enforcer"
    "database-designer"
    "frontend-developer"
    "ios-developer"
    "javascript-developer"
    "mobile-developer"
    "php-developer"
    "python-developer"
    "typescript-developer"
    "wordpress-developer"
)

echo "Verifying global subagents installation..."
echo "========================================="

missing_count=0
for agent in "${EXPECTED_AGENTS[@]}"; do
    if [ -f "$HOME/.claude/agents/$agent.md" ]; then
        echo "✓ $agent"
    else
        echo "✗ $agent (MISSING)"
        ((missing_count++))
    fi
done

echo "========================================="
if [ $missing_count -eq 0 ]; then
    echo "✅ All 17 agents successfully installed!"
else
    echo "⚠️  $missing_count agent(s) missing"
    exit 1
fi
```

### Testing Global Agent Access

To test that Claude Code can access your global agents:

1. Navigate to any project directory (not the one with local agents)
2. Open Claude Code
3. Try using a subagent command like `/ask @code-reviewer`
4. The global agent should be available and functional

## Best Practices

### 1. Version Control for Global Agents

Consider maintaining your global agents in a Git repository:

```bash
# Initialize version control for global agents
cd ~/.claude/agents
git init
git add *.md
git commit -m "Initial commit of global Claude Code subagents"

# Create a remote backup (e.g., on GitHub)
git remote add origin git@github.com:yourusername/claude-agents.git
git push -u origin main
```

### 2. Regular Backups

Create periodic backups of your global agents:

```bash
# Create timestamped backup
tar -czf ~/claude-agents-backup-$(date +%Y%m%d).tar.gz ~/.claude/agents/
```

### 3. Synchronization Across Machines

If you work on multiple machines, consider using a synchronization strategy:

```bash
# Using rsync to sync between machines
rsync -av ~/.claude/agents/ user@other-machine:~/.claude/agents/

# Or use a cloud storage service with symbolic links
ln -s ~/Dropbox/claude-agents ~/.claude/agents
```

### 4. Documentation Standards

Maintain consistent documentation within each agent file:
- Clear purpose statement at the beginning
- Version information if applicable
- Any special requirements or dependencies
- Examples of usage

## When to Use Local vs Global

### Use Global Subagents When:
- The agent represents a general development pattern (e.g., code-reviewer, python-developer)
- You want consistent behavior across all projects
- The agent doesn't contain project-specific information
- You frequently switch between projects and need the same tools
- Setting up standard development workflows for your team

### Use Local Subagents When:
- The agent contains project-specific configurations or rules
- You need to override a global agent's behavior for a specific project
- The agent references project-specific paths, APIs, or credentials
- You're experimenting with new agent configurations
- The project has unique requirements that differ from your standard workflow

### Hybrid Approach

You can use both global and local agents effectively:

```bash
# Example structure for a project using both
project/
├── .claude/
│   └── agents/
│       ├── project-api-spec.md      # Local: project-specific API agent
│       └── custom-linter.md         # Local: project-specific linting rules
└── src/
    └── ...

# Global agents still available:
~/.claude/agents/
├── python-developer.md              # Global: general Python patterns
├── code-reviewer.md                 # Global: standard review practices
└── ...
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Agents Not Appearing in Claude Code

**Problem**: Global agents aren't recognized by Claude Code

**Solutions**:
```bash
# Verify correct directory structure
ls -la ~/.claude/agents/

# Check file permissions
chmod 644 ~/.claude/agents/*.md

# Ensure files have .md extension
for f in ~/.claude/agents/*; do
    [[ "$f" == *.md ]] || echo "Warning: $f doesn't have .md extension"
done
```

#### 2. Permission Denied Errors

**Problem**: Cannot create or access global agents directory

**Solutions**:
```bash
# Fix directory permissions
chmod 755 ~/.claude
chmod 755 ~/.claude/agents

# Fix file permissions
chmod 644 ~/.claude/agents/*.md
```

#### 3. Conflicts Between Local and Global Agents

**Problem**: Unexpected behavior when both local and global agents exist

**Solution**: Remember that local agents take precedence. To use global version:
```bash
# Temporarily rename or remove local agent
mv .claude/agents/code-reviewer.md .claude/agents/code-reviewer.md.local

# Or explicitly reference the global agent in your workflow
```

#### 4. Agents Not Updating

**Problem**: Changes to global agents aren't reflected in Claude Code

**Solutions**:
- Restart Claude Code to ensure it picks up the latest changes
- Verify you're editing the correct file (global vs local)
- Check that the file was saved properly

### Diagnostic Commands

```bash
# Show all agent locations (local and global)
find . ~/.claude -name "*.md" -path "*/agents/*" 2>/dev/null

# Compare local and global agents
diff .claude/agents/code-reviewer.md ~/.claude/agents/code-reviewer.md

# Check last modification times
ls -lt ~/.claude/agents/*.md | head -5

# Verify agent content is valid
for agent in ~/.claude/agents/*.md; do
    head -n 1 "$agent" | grep -q "^#" || echo "Warning: $agent might not be properly formatted"
done
```

## Available Global Subagents

After successful migration, you'll have these 17 specialized subagents available globally:

### Development Subagents
- **api-developer**: REST API design and implementation
- **backend-developer**: Server-side application development
- **frontend-developer**: Client-side and UI development
- **database-designer**: Database schema and optimization

### Language-Specific Subagents
- **javascript-developer**: JavaScript/Node.js development
- **python-developer**: Python application development
- **typescript-developer**: TypeScript development with type safety
- **php-developer**: PHP web application development

### Mobile Development
- **ios-developer**: iOS/Swift application development
- **mobile-developer**: Cross-platform mobile development

### Code Quality Subagents
- **code-debugger**: Debugging and troubleshooting
- **code-documenter**: Documentation generation and maintenance
- **code-refactor**: Code refactoring and optimization
- **code-reviewer**: Code review and best practices
- **code-security-auditor**: Security vulnerability assessment
- **code-standards-enforcer**: Coding standards compliance

### Specialized Subagents
- **wordpress-developer**: WordPress development and customization

## Benefits of Global Subagents

### 1. Consistency Across Projects
- Uniform code standards and practices
- Consistent documentation format
- Standardized review processes

### 2. Reduced Setup Time
- No need to copy agents to each new project
- Instant access to all specialized agents
- Quick project initialization

### 3. Centralized Maintenance
- Update once, apply everywhere
- Single source of truth for agent configurations
- Easier version management

### 4. Resource Efficiency
- Less disk space usage (no duplicates)
- Cleaner project directories
- Simplified backup strategies

### 5. Team Collaboration
- Share standardized agents across team
- Consistent development experience
- Easier onboarding for new team members

### 6. Workflow Optimization
- Quick context switching between projects
- Consistent tool availability
- Reduced cognitive overhead

## Conclusion

Setting up global subagents for Claude Code significantly enhances your development workflow by providing consistent, readily available specialized assistants across all your projects. The migration process is straightforward and the benefits include improved consistency, reduced setup time, and easier maintenance.

Remember to:
- Keep global agents generic and project-agnostic
- Use local agents for project-specific customizations
- Maintain backups of your agent configurations
- Consider version controlling your agents for team sharing

With your 17 specialized subagents now available globally, you can leverage Claude Code's full potential across all your development projects without repetitive setup tasks.

---

*Last Updated: January 2025*
*Total Global Subagents: 17*
*Claude Code Version: Compatible with latest*