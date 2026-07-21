# Source Control Best Practices for Autonomous Agents

Autonomous agents must follow structured source control protocols to ensure code quality and system stability.

## Core Technology Standard

- **Standard:** Use Git as the primary version control system.
- **Workflow:** This project uses trunk-based development. There are no long-lived feature branches and no pull requests — all work is committed straight to the trunk (`main`) in small, frequent, atomic commits.

## Commit Guidelines

- **Direct to Trunk:** Commit directly to `main`. Do not create feature or bugfix branches.
- **Atomic Commits:** Bundle only related changes into a single commit. Prefer several small commits over one large one.
- **Commit Messages:** Write clear, imperative-tone messages (e.g., `feat: add retry logic to API client`).
- **Validation:** Run local linter and test suites before every commit. Never commit code that fails tests or linting.
- **Keep Trunk Healthy:** Because there is no branch isolation, every commit to `main` must leave the codebase in a working state.

## Test-Driven Development Workflow

For each task:

1. Write a test case upfront that captures the desired behavior.
2. Implement the code required to satisfy that test.
3. Run the full local test suite and linter to confirm nothing is broken.
4. Commit the change with a clear, atomic commit message.

## Review Workflow

There is no GitHub pull request process. Instead, review happens agent-to-agent, directly on the working code:

1. **Initial Output:** The builder agent completes a task (implementation plus tests) and commits it.
2. **Critique:** The reviewer agent inspects the builder's changes and produces feedback — noting any issues with coding standards, test coverage, security, performance, or adherence to the task definition.
3. **Apply Feedback:** The builder agent applies the reviewer's feedback directly to the working tree, or responds with a rationale if it disagrees with a specific point.
4. **Re-validation:** After applying feedback, the builder re-runs the test suite and linter before committing the follow-up changes.
5. **Completion:** Once the reviewer has no further feedback, the task is considered complete. No merge step is required since work already lives on `main`.
