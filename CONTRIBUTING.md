# Contributing

Thanks for helping improve HolyFHIR Personal EMR.

Because this project deals with health records, please be especially careful with privacy and security. Do not commit, upload, paste, screenshot, or attach real personal health information.

## Do Not Include Real Health Data

Never include real:

- Patient names, dates of birth, addresses, phone numbers, emails, MRNs, account numbers, or other identifiers
- Conditions, medications, allergies, immunizations, observations, encounters, notes, documents, PDFs, images, or lab results
- FHIR bundles, MyChart exports, portal downloads, database files, backups, logs, or screenshots from actual use
- Passwords, recovery keys, `.env` files, encryption keys, access tokens, cookies, or session data

Use synthetic data only. Make sample data obviously fake.

## Before Opening An Issue

- Search existing issues first.
- Describe the problem clearly.
- Include steps to reproduce with synthetic data.
- Remove secrets, local paths, and any sensitive health information from logs.
- Do not attach database files, exports, screenshots, or medical documents from real use.

## Before Opening A Pull Request

- Keep changes focused.
- Add or update tests when behavior changes.
- Update documentation when user-facing behavior changes.
- Check that generated files, local databases, uploads, logs, installer artifacts, and secrets are not included.
- Review the diff carefully for accidental health information or credentials.

## Security Issues

Please do not open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md).
