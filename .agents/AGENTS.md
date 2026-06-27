# GridLens - AI Agent Guidelines

## 1. Project Context
- **Name:** GridLens
- **Purpose:** A desktop application that converts photographed or scanned spreadsheets into structured digital files (CSV or Excel).
- **Core Spec:** Always refer to `spreadsheet_scanner_app_spec.md` for architectural, design, and feature requirements before implementing new features.
- **Primary Language:** Python

## 2. Core Directives
- **Change Tracking:** Always document any significant architectural changes, bug fixes, or feature additions in `CHANGELOG.md`. The user specifically requested tracking of changes over time.
- **Maintain Documentation:** When modifying code, ensure inline docstrings and comments are updated to reflect the logic changes.
- **Project Structure:** Follow the existing module structures (`core/`, `ui/`, etc.) defined in the project unless refactoring is explicitly requested.
- **Testing:** Verify changes locally via `main.py` or the provided build scripts before declaring a feature complete.

## 3. Communication Style & Workflow
- **Proactive Review:** Read the relevant sections of `spreadsheet_scanner_app_spec.md` prior to beginning a large refactor or feature addition.
- **Concise Reporting:** When summarizing work, link to the specific files modified and point out any open questions.
