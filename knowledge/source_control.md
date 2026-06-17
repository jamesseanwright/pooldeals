# Source Control Best Practices for Autonomous Agents

Autonomous agents must follow structured source control protocols to ensure code quality, system stability, and seamless human-agent collaboration.

## Core Technology Standard

- **Standard:** Use Git as the primary version control system.
- **Hosting Platform:** Use GitHub for repository hosting and collaboration.

## Branching Strategy

- **Protected Branch:** Never commit directly to the `main` or `master` branch.
- **Feature Branches:** Create a new branch for every isolated task.
- **Naming Convention:** Use the format `feature/task-description` or `bugfix/issue-number`.

## Commit Guidelines

- **Atomic Commits:** Bundle only related changes into a single commit.
- **Commit Messages:** Write clear, imperative-tone messages (e.g., `feat: add retry logic to API client`).
- **Validation:** Run local linter and test suites before committing code.

## Pull Request (PR) Protocol

Agents must raise a GitHub Pull Request immediately after completing a task.

### 1. PR Creation

- **Target Branch:** Set the base branch to `main`.
- **Title:** Summarize the change concisely.
- **Description:** Provide a clear summary of what was changed and why.

### 2. Automation and Testing

- **CI/CD:** Verify that all automated GitHub Actions pass.
- **Conflicts:** Resolve any merge conflicts with the base branch autonomously.

### 3. Review and Merge

- **Reviewers:** Assign human supervisors or peer agents to review the code.
- **Merging:** Do not merge until all automated checks pass and approvals are secured.

## Handling Pull Request Feedback

Agents must process feedback from human reviewers or other validation agents systematically.

### 1. Review Analysis

- **Parse Comments:** Extract actionable requests from PR line comments.
- **Acknowledge:** Reply to the comment to confirm the feedback is understood.
- **Clarify:** Prompt the reviewer if instructions are ambiguous or contradictory.

### 2. Implementing Changes

- **Local Fixes:** Apply required changes directly to the active feature branch.
- **Test Verification:** Re-run local test suites to ensure fixes do not introduce regressions.
- **Push Updates:** Push new commits to the same branch to automatically update the PR.

### 3. Resolving the Review

- **Thread Resolution:** Mark comment threads as resolved once changes are pushed.
- **Re-request Review:** Trigger a formal re-review request on GitHub if required.
