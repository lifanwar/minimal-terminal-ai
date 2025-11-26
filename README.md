# Perplexity AI Terminal

Interactive terminal interface for Perplexity AI with filesystem navigation and context-aware file handling. Navigate your filesystem, add files to context, and query AI with full codebase awareness.

## ✨ Features

- 🗂️ **Filesystem Navigation** - Unix-like commands: `ls`, `cd`, `pwd`, `cat`, `tree`
- 📋 **Context Management** - Add files to AI context with `@add`, `@remove`, `@list`, `@clear`
- 🤖 **AI Query with Context** - Ask questions about your code with full file context
- 🔒 **Safe Boundaries** - Access limited to home directory for security
- 🎨 **Rich UI** - Beautiful terminal interface with syntax highlighting
- ⚡ **Glob Pattern Support** - Add multiple files with wildcards (`*.py`, `src/**/*.js`)

### Prerequisites                                                              
                                                                                
 - Python 3.12 or higher                                                        
 - Perplexity AI account with valid cookies                                     
 - Nix package manager (optional, for Nix users)

## 🚀 Quick Start

### Installation

~ > cd projects/myapp
✓ ~/projects/myapp

~/projects/myapp > ls
📁 src/
📁 tests/
📄 README.md (2.1KB)
📄 requirements.txt (456B)

~/projects/myapp > cd src

~/projects/myapp/src > @add *.py
✓ Added 8 file(s) to context

~/projects/myapp/src > @list
📋 Context (8 files, 15.3KB)
  -  main.py (2.1KB)
  -  utils.py (1.8KB)
  ...

~/projects/myapp/src > explain how the authentication works in this codebase
[AI akan analyze 8 files dalam context]

~/projects/myapp/src > @clear
✓ Context cleared

~/projects/myapp/src > cd ..

~/projects/myapp > cat README.md
[Shows README content]
