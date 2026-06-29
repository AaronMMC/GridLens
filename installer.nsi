; GridLens — NSIS Installer Script
; ===================================
;
; This script is designed to be compiled with NSIS (Nullsoft Scriptable
; Install System).  To build:
;
;   1. First build the exe:        build.bat
;   2. Then compile the installer: makensis installer.nsi
;
; Or use build_installer.bat which automates both steps.
;
; Override the version from the command line:
;   makensis /DVERSION=1.0.0 installer.nsi
;
; If VERSION is not defined it falls back to "1.0.0".  The
; build_installer.bat helper reads the true version from core/version.py
; and passes it automatically.
;

!define /ifndef VERSION "1.0.0"
!define APP_NAME "GridLens"
!define PUBLISHER "Aaron Miguel Cardenas"
!define EXE_NAME "${APP_NAME}.exe"
!define SETUP_NAME "${APP_NAME}_Setup_v${VERSION}.exe"

Name "${APP_NAME} v${VERSION}"
OutFile "dist\${SETUP_NAME}"
InstallDir "$PROGRAMFILES\${APP_NAME}"
RequestExecutionLevel admin

; ── Interface settings ──────────────────────────────────────────────────────

!include "MUI2.nsh"
!include "FileFunc.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${APP_NAME} v${VERSION} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will install ${APP_NAME} v${VERSION} on your computer.$\r$\n$\r$\n${APP_NAME} is an AI-powered desktop application that converts photographs and scanned documents into structured spreadsheets."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXE_NAME}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APP_NAME} v${VERSION}"

; ── Pages ───────────────────────────────────────────────────────────────────

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ── Languages ───────────────────────────────────────────────────────────────

!insertmacro MUI_LANGUAGE "English"

; ── Install section ─────────────────────────────────────────────────────────

Section "Install ${APP_NAME}" SecMain
    SetOutPath "$INSTDIR"

    ; Main executable
    File "dist\${EXE_NAME}"

    ; Application icon
    File /nonfatal "assets\icon.ico"

    ; .env.example — user copies to .env and edits
    File /nonfatal ".env.example"

    ; Write version info to registry for display in Apps & Features
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "DisplayIcon" "$INSTDIR\icon.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "InstallLocation" "$INSTDIR"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "NoRepair" 1

    ; Estimate size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "EstimatedSize" "$0"

    ; Start Menu shortcut
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${EXE_NAME}" \
        "" "$INSTDIR\icon.ico" 0 SW_SHOWNORMAL
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk" "$INSTDIR\uninstall.exe"

    ; Desktop shortcut (optional — user can delete)
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${EXE_NAME}" \
        "" "$INSTDIR\icon.ico" 0 SW_SHOWNORMAL

    ; Write the uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; ── Uninstall section ───────────────────────────────────────────────────────

Section "Uninstall"
    ; Remove shortcuts
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk"
    RmDir "$SMPROGRAMS\${APP_NAME}"

    Delete "$DESKTOP\${APP_NAME}.lnk"

    ; Remove installed files
    Delete "$INSTDIR\${EXE_NAME}"
    Delete "$INSTDIR\icon.ico"
    Delete "$INSTDIR\.env.example"
    Delete "$INSTDIR\uninstall.exe"
    RmDir "$INSTDIR"

    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd
