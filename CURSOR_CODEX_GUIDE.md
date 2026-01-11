# How to Use Codex/Chat in Cursor

## You're Already Using It! 🎉

You're currently chatting with me - that's Cursor's AI assistant (formerly called "Codex"). Here's how to use it effectively:

## Basic Usage

### 1. **Chat Panel** (What you're using now)
- **Open:** Press `Cmd+L` (Mac) or `Ctrl+L` (Windows/Linux)
- **Or:** Click the chat icon in the sidebar
- **Or:** Click the "Chat" button in the top toolbar

### 2. **Inline Chat** (Quick context-aware help)
- **Open:** Press `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux)
- **Use:** Ask questions about specific code you're viewing
- **Best for:** Quick edits, explanations of code blocks

### 3. **Composer** (Multi-file editing)
- **Open:** Press `Cmd+I` (Mac) or `Ctrl+I` (Windows/Linux)
- **Use:** Ask for changes across multiple files
- **Best for:** Large refactors, adding features

## Tips for Better Results

### ✅ **DO:**
- Be specific: "Fix the deliver action to show food requirements"
- Reference files: `@filename.py` to include context
- Use code snippets: Paste code in your message
- Break down tasks: Ask for one thing at a time
- Give context: Explain what you're trying to achieve

### ❌ **DON'T:**
- Be too vague: "Fix the code" (what code? what's wrong?)
- Ask for everything at once: Break it down
- Forget to review: Always check the changes I make

## Examples

### Good Prompt:
```
"Look at @lambda_labs_agent.py and fix the act() method to accept episode_history parameter and show action outcomes in the prompt"
```

### Better Prompt:
```
"In @manipulation_sim/lambda_labs_agent.py, the act() method needs to:
1. Accept episode_history parameter
2. Show previous day's actions and outcomes
3. Display why actions failed (e.g., 'failed: no food')

Update the method signature and prompt construction."
```

### Great Prompt (what we just did!):
```
"Agents keep trying to deliver with no food. Add action feedback so they see when actions fail. Pass episode_history to act() and show outcomes in prompts."
```

## Keyboard Shortcuts Summary

| Action | Mac | Windows/Linux |
|--------|-----|---------------|
| Open Chat | `Cmd+L` | `Ctrl+L` |
| Inline Edit | `Cmd+K` | `Ctrl+K` |
| Composer | `Cmd+I` | `Ctrl+I` |
| Accept Suggestion | `Tab` | `Tab` |
| Dismiss | `Esc` | `Esc` |

## Features You're Using

- ✅ **Chat** - You're using this now!
- ✅ **Code context** - I can see your files
- ✅ **Code editing** - I can edit files for you
- ✅ **File reading** - I can read and analyze code
- ✅ **Terminal access** - I can run commands

## Current Experiment Status

Your experiment is now running with the fixes! Monitor it with:

```bash
tail -f experiment_fixed_v2.log
```

The agents should now:
- See their action history
- Learn from failures
- Show more manipulation behavior
- Talk more and do different actions
