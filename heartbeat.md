# AlphaEdge Heartbeat Directive

This file drives the 24/7 background automation loop of AlphaEdge. The `MetaManager` periodically reads this file to decide what autonomous tasks to dispatch to Jules AI or what local skills to execute.

## Current Objectives
1. **System Health Check**: Ensure all tests pass.
2. **Feature Development**: 
   - Integrate `Scrapling` (https://github.com/D4Vinci/Scrapling) into a skill. Read the documentation via web search, and author a new Python script inside the `skills` directory that scrapes basic web content.
3. **Continuous Refactoring**: Address any local Git unstaged or uncommitted changes that break tests.
