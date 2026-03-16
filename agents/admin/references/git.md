# Git Workflow and Commit Standards

This guide documents the standardized Git workflow and commit requirements for the homelab.

## Branching and Pull Requests

- **Never push directly to the main branch**: All changes must be made in a separate branch and submitted via a Pull Request (PR) for review and validation.
- **Sync with main before starting**: Always checkout the `main` branch and run `git pull` before creating a new feature or fix branch to ensure you are working from the latest state.
- **Merge Conflicts**: If conflicts arise, they must be merged and resolved locally on your branch before the PR can be merged to `main`.
- **PR Descriptions**: Provide a clear description of the change, why it was made, and any verification steps performed.
    - Quick summary of changes
    - What was changed
    - Why it was changed
    - Any verification steps performed
    - Add details like docker image, chart, versions used
    - Format with bullet points, headers or emojis

## Commit Standards

The homelab uses **Conventional Commits** paired with **Gitmoji** to ensure a readable and well-categorized history.

### Conventional Commits
Follow the specification at [conventionalcommits.org](https://www.conventionalcommits.org/):
- `feat`: A new feature (e.g., installing a new app).
- `fix`: A bug fix (e.g., correcting a manifest error).
- `chore`: Maintenance tasks or dependency updates.
- `docs`: Documentation changes.
- `refactor`: Code changes that neither fix a bug nor add a feature.

### Gitmoji
Inject the appropriate gitmoji at the start of the commit message (see [gitmoji.dev](https://gitmoji.dev/)):
- ✨ `:sparkles:` for new features.
- 🐛 `:bug:` for bug fixes.
- 🔒 `:lock:` for security/secrets changes.
- 📝 `:memo:` for documentation.
- ♻️ `:recycle:` for refactoring.

### Example Commit Message
`✨ feat(apps): add actual-budget to homelab`
