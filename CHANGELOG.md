# Changelog

All notable changes to the GridLens project will be documented in this file.

## [Unreleased]

### Added
- Created `.agents/AGENTS.md` to establish rules and context for AI coding assistants.
- Initialized `CHANGELOG.md` to track ongoing changes as requested.
- Renamed project to GridLens.
- Added Gemini (free tier) as a backend for higher accuracy.
- Improved app responsiveness by showing setup wizard before main window load.
- Added `ui/crop_dialog.py` – image cropping dialog with rubber-band rectangle selection, dark-purple theme, and JPEG output.
- Created `core/version.py` as the single source of truth for the application version.
- Added Windows VERSIONINFO resource (`version_info.txt`) embedded into the exe via PyInstaller.
- Implemented `GridLens.spec` — PyInstaller spec that auto-generates version metadata from `core/version.py`.
- Implemented `installer.nsi` — NSIS installer script with version awareness, Start Menu shortcuts, and uninstall support.
- Added `build_installer.bat` to automate building the NSIS installer from the spec.
- Updated `build.bat` / `build.ps1` to use the spec file for consistent builds.
- Added module-level docstrings to every Python source file and build script.
