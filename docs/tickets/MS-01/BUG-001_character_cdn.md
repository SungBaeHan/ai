# BUG-001 Character Image CDN Domain Error

## Metadata

Severity: major  
Layer: adapter  
Milestone: MS-01_Stabilization  

---

## Description

Character images are currently being served using the R2 development public URL.

Current:

https://pub-xxxx.r2.dev/assets/char/{id}.png

Expected:

https://img.arcanaverse.ai/assets/char/{id}.png

This violates CDN policy and branding rules.

---

## Reproduction

1. Open home
2. Go to character selection
3. Open browser devtools
4. Inspect image URL

---

## Expected Result

All character images should use the CDN base domain.


https://img.arcanaverse.ai/assets/char/{id}.png


---

## Actual Result

Images are returned from:


https://pub-xxxx.r2.dev/assets/char/{id}.png


---

## Environment

env: dev  
browser: Chrome  
device: Desktop  

---

## Technical Context

Possible locations:

apps/api/utils/common.py  
apps/api/config.py  
adapters/file_storage/r2_storage.py  

The project already contains a CDN configuration:


ASSET_BASE_URL


Image URLs should use that base.

---

## Implementation Strategy

Do NOT modify:

- database schema
- infra configuration
- storage upload logic

Fix only the public URL generation.

Prefer:


ASSET_BASE_URL + asset_path


---

## Acceptance Criteria

1. Character image URL must start with


https://img.arcanaverse.ai


2. R2 public domain must not appear in API responses.

3. Existing functionality must remain unchanged.

---

## Verification

1. Start API
2. Open character list
3. Inspect network tab
4. Confirm CDN domain is used

---

## Output Format

Before coding provide:

- root cause
- files to change
- implementation plan

After coding provide:

- files changed
- summary
- verification steps
- risks