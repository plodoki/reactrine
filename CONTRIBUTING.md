# Contributing to Reactrine

We love receiving contributions from the community and are thrilled that you're interested in helping us improve the Reactrine. This document will guide you through the contribution process.

## Code of Conduct

We are committed to fostering an open, welcoming, and inclusive environment, and we expect all contributors to adhere to these standards.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on our GitHub repository. When you do, please include:

- A clear and descriptive title.
- A detailed description of the problem, including the steps to reproduce it.
- The expected behavior and what actually happened.
- Your operating system, browser, and any other relevant environment details.

### Suggesting Enhancements

If you have an idea for a new feature or an improvement to an existing one, we'd love to hear about it. Please open an issue and provide:

- A clear and descriptive title.
- A step-by-step description of the suggested enhancement.
- A detailed explanation of why this enhancement would be useful.

## Development Workflow

1.  **Fork the Repository** and clone it to your local machine.
2.  **Create a Feature Branch** from the `main` branch:
    ```bash
    git checkout -b feature/your-awesome-feature
    ```
3.  **Set Up the Development Environment:**
    ```bash
    just setup
    ```
4.  **Make Your Changes:**
    - Write clean, readable, and maintainable code.
    - Follow the existing code style and architecture patterns.
    - Write tests for any new functionality or bug fixes.
5.  **Run Quality Checks:**
    Before committing your changes, please run all the quality checks to ensure your code is ready for review.
    ```bash
    just format
    just lint
    just typecheck
    just test
    ```
6.  **Commit Your Changes** using the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) standard.
    ```bash
    git commit -m "feat: Add new awesome feature"
    ```
7.  **Push to Your Fork** and open a pull request to the `main` branch of the original repository.

## Pull Request Process

1.  Provide a clear title and a detailed description of the changes in your pull request. If it addresses an open issue, please reference it (e.g., "Closes #123").
2.  The maintainers will review your pull request. All automated checks (linting, tests, etc.) must pass.
3.  Be responsive to any feedback or requested changes from the reviewers.
4.  Once the pull request is approved, a maintainer will merge it into the `main` branch.

We appreciate your contributions and look forward to building a better boilerplate together!
