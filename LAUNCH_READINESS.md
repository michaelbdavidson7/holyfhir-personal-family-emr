# HolyFHIR Launch Readiness

HolyFHIR is close to a trusted early beta, not a broad public launch yet.

Because the app handles family health information, launch should be staged. The first public promise should be modest and true: an early local Windows app for organizing personal and family health records, especially MyChart/FHIR exports, with clear limits.

## Recommended Launch Stage

Launch first as a **trusted early Windows build for personal and family recordkeeping**.

Avoid positioning it as:

- a finished medical product
- a replacement for MyChart, doctors, pharmacies, hospitals, or official records
- a certified EHR/EMR
- an emergency tool
- a clinical decision support tool

Good launch language:

> HolyFHIR is an early local health record organizer for families who want a private copy of their records on their own computer.

## Must-Have Before Trusted Beta

- First-run desktop startup shows visible progress while setup and migrations run.
- Rapid double-click / repeated launch does not corrupt startup or migrations.
- Dashboard first impression is calm and clear.
- Dashboard explains both starting paths:
  - import records from MyChart/FHIR when available
  - manually add someone when portal records are not available
- MyChart import can create a person automatically.
- Manual person setup works without requiring MyChart.
- Users can see where their local data lives.
- Users get clear password and recovery-key instructions.
- Users understand there is no cloud reset if local credentials/recovery material are lost.
- Users see an in-app disclaimer that this is not medical advice or emergency information.
- Users are warned to verify important information against official sources.
- Users know to keep original records from doctors, hospitals, pharmacies, labs, and portals.

## Trust And Privacy Basics

- Explain clearly that the app is local-first and does not require a cloud account.
- Explain what is stored locally.
- Explain what is encrypted.
- Explain what is not encrypted, especially uploaded documents if they are outside the encrypted database.
- Confirm database, media, log, backup, and export locations in the packaged Windows app.
- Make sure logs do not include secrets or health information.
- Give users a safe way to report bugs without sending real health data.
- Add plain guidance for deleting local data.
- Add plain guidance for exporting data before uninstalling.

## Backup And Recovery Bar

Before a wider launch, the app needs a backup story that a non-technical user can follow.

Minimum acceptable beta state:

- Tell users exactly which files/folders matter.
- Tell users to back up before uninstalling or upgrading.
- Tell users to save password and recovery material separately.
- Warn that losing password/encryption/recovery material can make data unrecoverable.

Before public launch:

- Add backup creation flow.
- Add restore flow.
- Test restore on a clean install.
- Confirm backups include the database and any uploaded documents.
- Add backup/export warning before risky operations.

## Import Readiness

- Test MyChart ZIP import from a clean install.
- Test FHIR JSON Bundle import.
- Test single-resource JSON import.
- Test NDJSON import if exposed.
- Test invalid JSON, missing `resourceType`, broken ZIPs, and oversized files.
- Show import results in plain language:
  - people created
  - records imported
  - records saved only as raw FHIR
  - invalid or skipped records
  - unresolved references
- Keep the raw FHIR snapshot as source traceability.
- Avoid silently discarding data.

## Export And Sharing

- Make export modes clear:
  - raw imported FHIR
  - app-created/model-serialized FHIR
  - human-readable medical summary PDF
- Warn that exported data may be technical, incomplete, or transformed.
- Add a simple "share with your doctor" guide.
- Add "what is included" and "what may be missing" notes.
- Add privacy warning before exporting ZIP/PDF files.

## Desktop Packaging

- Verify clean install.
- Verify upgrade with an existing database.
- Verify startup with pending migrations.
- Verify app behavior with no network.
- Verify static files work in release build.
- Verify release build behavior with `DEBUG=False`.
- Verify installer places files where expected.
- Verify uninstall does not surprise-delete user data, or clearly warns users first.
- Add visible app version.
- Add release notes/changelog.
- Sign the Windows installer before broad public distribution if possible.

## Product Polish

The first dashboard screen should answer:

- What is this?
- What do I do first?
- What if I do not use MyChart?
- Is my data private/local?
- Where do I go after importing?

Keep trimming anything that feels like Django/admin plumbing from the normal user path. Advanced FHIR/admin tools can exist, but they should not dominate the first impression.

## Wider Public Launch Gate

Do not launch broadly until these are true:

- Backup and restore are tested end to end.
- Clean install and upgrade paths are tested.
- MyChart import has been tested with multiple synthetic examples.
- Import failure states are understandable.
- Release build is tested outside the development machine.
- In-app disclaimers and limitation notes are visible.
- Security/privacy docs match actual behavior.
- Users can report issues without exposing personal health information.
- You are comfortable with the support burden for people storing real family health data.

## Post-Beta Improvements

- Import preview before committing data.
- Import history and rollback/delete-import-batch flow.
- Better duplicate patient/resource detection.
- Patient matching review UI.
- Clear imported-vs-manual data labels.
- Medical summary PDF improvements.
- Emergency/paramedic summary view.
- Accessibility pass.
- Signed installer and auto-update strategy.
