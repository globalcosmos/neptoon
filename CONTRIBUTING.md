<!-- omit in toc -->
# Contributing to neptoon

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution. It will make it a lot easier for us maintainers and smooth out the experience for all involved. The community looks forward to your contributions. 🎉

> And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation, which we would also be very happy about:
> - Star the project
> - Tweet about it
> - Refer this project in your project's readme
> - Mention the project at local meetups and tell your friends/colleagues

<!-- omit in toc -->
## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [I Have a Question](#i-have-a-question)
  - [I Want To Contribute](#i-want-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Improving The Documentation](#improving-the-documentation)
- [Styleguides](#styleguides)
  - [Commit Messages](#commit-messages)
- [Join The Project Team](#join-the-project-team)


## Code of Conduct

This project and everyone participating in it is governed by the
[neptoon Code of Conduct](https://codebase.helmholtz.cloud/cosmos/neptoon/blob/main/CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code. Please report unacceptable behavior
to <>.


## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://www.neptoon.org).

Before you ask a question, it is best to search for existing [Issues](https://codebase.helmholtz.cloud/cosmos/neptoon/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue. It is also advisable to search the internet for answers first.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Open an [Issue](https://codebase.helmholtz.cloud/cosmos/neptoon/issues/new).
- Or send an email to contact@neptoon.org
- Provide as much context as you can about what you're running into.
- Provide project and platform versions, depending on what seems relevant.

We will then take care of the issue as soon as possible.

<!--
You might want to create a separate issue tag for questions and include it in this description. People should then tag their issues accordingly.

Depending on how large the project is, you may want to outsource the questioning, e.g. to Stack Overflow or Gitter. You may add additional contact and information possibilities:
- IRC
- Slack
- Gitter
- Stack Overflow tag
- Blog
- FAQ
- Roadmap
- E-Mail List
- Forum
-->

## I Want To Contribute

> ### Legal Notice <!-- omit in toc -->
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project licence.

### Reporting Bugs

<!-- omit in toc -->
#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to investigate carefully, collect information and describe the issue in detail in your report. Please complete the following steps in advance to help us fix any potential bug as fast as possible.

- Make sure that you are using the latest version.
- Determine if your bug is really a bug and not an error on your side e.g. using incompatible environment components/versions (Make sure that you have read the [documentation](https://www.neptoon.org). If you are looking for support, you might want to check [this section](#i-have-a-question)).
- To see if other users have experienced (and potentially already solved) the same issue you are having, check if there is not already a bug report existing for your bug or error in the [bug tracker](https://codebase.helmholtz.cloud/cosmos/neptoon/issues?q=label%3Abug).
- Also make sure to search the internet (including Stack Overflow) to see if users outside of the GitHub community have discussed the issue.
- Collect information about the bug:
  - Stack trace (Traceback)
  - OS, Platform and Version (Windows, Linux, macOS, x86, ARM)
  - Version of the interpreter, compiler, SDK, runtime environment, package manager, depending on what seems relevant.
  - Possibly your input and the output
  - Can you reliably reproduce the issue? And can you also reproduce it with older versions?

<!-- omit in toc -->
#### How Do I Submit a Good Bug Report?

> You must never report security related issues, vulnerabilities or bugs including sensitive information to the issue tracker, or elsewhere in public. Instead sensitive bugs must be sent by email to <>.
<!-- You may add a PGP key to allow the messages to be sent encrypted as well. -->

We use GitLab issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://codebase.helmholtz.cloud/cosmos/neptoon/issues/new). (Since we can't be sure at this point whether it is a bug or not, we ask you not to talk about a bug yet and not to label the issue.)
- Explain the behavior you would expect and the actual behavior.
- Please provide as much context as possible and describe the *reproduction steps* that someone else can follow to recreate the issue on their own. This usually includes your code. For good bug reports you should isolate the problem and create a reduced test case.
- Provide the information you collected in the previous section.

<!-- You might want to create an issue template for bugs and errors that can be used as a guide and that defines the structure of the information to be included. If you do so, reference it here in the description. -->


### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for neptoon, **including completely new features and minor improvements to existing functionality**. Following these guidelines will help maintainers and the community to understand your suggestion and find related suggestions.

<!-- omit in toc -->
#### Before Submitting an Enhancement

- Make sure that you are using the latest version.
- Read the [documentation](https://www.neptoon.org) carefully and find out if the functionality is already covered, maybe by an individual configuration.
- Perform a [search](https://codebase.helmholtz.cloud/cosmos/neptoon/issues) to see if the enhancement has already been suggested. If it has, add a comment to the existing issue instead of opening a new one.
- Find out whether your idea fits with the scope and aims of the project. It's up to you to make a strong case to convince the project's developers of the merits of this feature. Keep in mind that we want features that will be useful to the majority of our users and not just a small subset. If you're just targeting a minority of users, consider writing an add-on/plugin library.

<!-- omit in toc -->
#### How Do I Submit a Good Enhancement Suggestion?

Enhancement suggestions are tracked as [GitLab issues](https://codebase.helmholtz.cloud/cosmos/neptoon/issues).

- Use a **clear and descriptive title** for the issue to identify the suggestion.
- Provide a **step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why. At this point you can also tell which alternatives do not work for you.
- You may want to **include screenshots or screen recordings** which help you demonstrate the steps or point out the part which the suggestion is related to. You can use [LICEcap](https://www.cockos.com/licecap/) to record GIFs on macOS and Windows, and the built-in [screen recorder in GNOME](https://help.gnome.org/users/gnome-help/stable/screen-shot-record.html.en) or [SimpleScreenRecorder](https://github.com/MaartenBaert/ssr) on Linux. <!-- this should only be included if the project has a GUI -->
- **Explain why this enhancement would be useful** to most neptoon users. You may also want to point out the other projects that solved it better and which could serve as inspiration.

<!-- You might want to create an issue template for enhancement suggestions that can be used as a guide and that defines the structure of the information to be included. If you do so, reference it here in the description. -->

### Your First Code Contribution

Ready to contribute code to neptoon? Follow these steps to set up your development environment and make your first contribution.

#### Setting Up Your Development Environment

1. **Fork the repository**
   - Visit [gitlab.com/neptoon/neptoon](https://www.gitlab.com/neptoon/neptoon) (our public mirror)
   - Click "Fork" to create your own copy of the repository

2. **Clone your fork locally**
   ```bash
   git clone https://gitlab.com/YOUR_USERNAME/neptoon.git
   cd neptoon
   ```

3. **Set up your IDE with code formatting**
   - We use Black for code formatting
   - **VS Code**: Install the Black Formatter extension and add to your settings.json:
     ```json
     {
         "python.defaultInterpreterPath": "./venv/bin/python",
         "[python]": {
             "editor.formatOnSave": true,
             "editor.defaultFormatter": "ms-python.black-formatter"
         }
     }
     ```
   - **Other IDEs**: Search for "Black formatter setup" for your preferred editor

4. **Create and switch to a feature branch**
   ```bash
   git checkout -b my-feature-name
   ```
   Use descriptive branch names like `fix-memory-leak` or `add-plotting-utils`

5. **Set up your Python environment**
   ```bash
   # Using uv (recommended)
   uv venv
   source ./bin/activate  # On Windows: venv\Scripts\activate
   uv pip install -e .
   
   # Or using standard pip
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   ```
   The `-e` flag installs in "editable" mode so your code changes are immediately available.

6. **Create your testing workspace**
   ```bash
   mkdir test_dir
   ```
   Use `test_dir/` for personal notebooks, test scripts, and development notes. This directory is git-ignored and won't appear in your commits.

7. **Verify your setup**
   ```bash
   python -c "import neptoon; print('Setup successful!')"
   ```

#### Making Your Changes

- Write your code following existing patterns in the codebase
- Add tests for new functionality
- Update documentation if needed (see below)
- Use `test_dir/` for experimenting and validating your changes

#### Testing Your Changes

Before submitting, make sure your code works correctly:

```bash
# Run existing tests
pytest

# Test your changes manually in test_dir/
python test_dir/my_test_script.py
```

#### Updating Documentation

If your changes affect user-facing functionality, update the documentation:

1. **Edit relevant markdown files** in the `docs/` folder
2. **Add new pages** if needed and include them in `mkdocs.yml` under the `nav` section
3. **Preview your changes locally**:
   ```bash
   # Install documentation dependencies
   uv pip install -r requirements-docs.txt
   
   # Serve docs locally (auto-updates on save)
   mkdocs serve
   ```
   Visit the local URL shown to preview your documentation changes

#### Submitting Your Contribution

When you're ready to submit:

1. **Push your changes**
   ```bash
   git add .
   git commit -m "Brief description of your changes"
   git push origin my-feature-name
   ```

2. **Create a merge request**
   - Go to your fork on [gitlab.com/neptoon/neptoon](https://gitlab.com/neptoon/neptoon)
   - Click "Create merge request"
   - Target the merge request to the **public mirror** (gitlab.com/neptoon/neptoon)

3. **Notify the team**
   - Send an email to contact@neptoon.org mentioning your merge request
   - We monitor the public mirror but email ensures faster response

The maintainers will review your contribution and sync approved changes to our main development repository.

### Improving The Documentation

Want to improve our documentation? This guide is for contributors who want to fix typos, clarify explanations, expand descriptions, or add new documentation pages.

#### Quick Setup for Documentation Changes

1. **Fork and clone the repository**
   - Visit [gitlab.com/neptoon/neptoon](https://www.gitlab.com/neptoon/neptoon)
   - Click "Fork" to create your own copy
   - Clone locally:
     ```bash
     git clone https://gitlab.com/YOUR_USERNAME/neptoon.git
     cd neptoon
     ```

2. **Create a documentation branch**
   ```bash
   git checkout -b improve-docs-section-name
   ```

3. **Set up local preview** (no full Python environment needed)
   ```bash
   # Install only documentation dependencies
   pip install -r requirements-docs.txt
   
   # Start local documentation server
   mkdocs serve
   ```
   This creates a local preview at `http://127.0.0.1:8000` that auto-updates when you save changes

4. **Make your changes** to markdown files in the `docs/` folder

5. **Submit your changes**
   ```bash
   git add .
   git commit -m "Improve documentation: brief description"
   git push origin improve-docs-section-name
   ```
   Then create a merge request on GitLab and email contact@neptoon.org

#### Understanding the Documentation Structure

**MKDocs Setup**
- We use MKDocs with the Material theme
- Configuration is controlled by `mkdocs.yml` in the root directory
- All documentation content lives in the `docs/` folder

**Navigation Structure**
- The website menu is organized under the `nav` section in `mkdocs.yml`
- To add new pages: create a markdown file in `docs/` and add it to the `nav` section
- Look at the existing `nav` structure and the website to understand the organisation

**Local Development**
- `mkdocs serve` creates a local server that auto-refreshes on file changes
- Perfect for trying out styles and seeing changes immediately
- The local URL will be shown in your terminal when you run the command

#### Key Points to Remember

- **Markdown format**: All documentation uses standard Markdown with MKDocs Material extensions
- **Structure matters**: Check that your changes fit logically with the existing navigation and content flow

#### When to Contribute Documentation

- **Clarification**: When existing docs are unclear or confusing
- **Completeness**: When you notice missing information or examples
- **Accuracy**: When you find outdated or incorrect information
- **Accessibility**: When content could be more beginner-friendly

For questions about documentation contributions, reach out to contact@neptoon.org


## Join The Project Team

Drop an email to contact@neptoon.org 

<!-- omit in toc -->
## Attribution
This guide is based on the [contributing.md](https://contributing.md/generator)!
