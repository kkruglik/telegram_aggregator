# Create Pull Request

Create a comprehensive pull request for the current branch: $ARGUMENTS

## Steps  
1. Ensure all changes are committed and pushed
2. Run `git log --oneline -5` to see recent commits
3. Analyze the commits to understand the changes made
4. Use GitHub CLI to create PR: `gh pr create`
5. Generate a comprehensive PR description including:
   - **Summary**: Brief description of changes
   - **Changes Made**: Detailed list of modifications
   - **Breaking Changes**: Any breaking changes (if applicable)
6. Add appropriate labels and reviewers
7. Set milestone if applicable
8. Be concise

**Follow PR template structure and enforce title conventions**