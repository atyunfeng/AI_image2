# M4 Single-Image Editor Implementation Plan

**Goal:** Let an operator branch any generated image into an auditable edit project, perform masked AI edits or deterministic layout/text edits, compare immutable revisions, and send each result through quality evidence and human review.

**Architecture:** Add an `editing` domain containing edit projects, immutable revisions, masks, layers, and evidence. AI operations (`inpaint`, `outpaint`, `remove_background`) reuse the existing durable generation batch/step/worker pipeline with the exact source and processed mask assets in the snapshot. Deterministic transforms and authoritative text/logo layers create derived assets server-side without a model call. Every revision points to its parent and never overwrites an asset.

**Scope:**

- Source image selection from an existing generated batch.
- Canvas mask brush, erase, invert, dilation, feathering, and clear.
- Masked replace/remove, background replacement, and outpainting routed by provider capability.
- Deterministic move, scale, rotate, crop/background blur controls plus authoritative text and uploaded Logo layers.
- Immutable revision tree, undo/redo navigation, snapshot labels, and before/after comparison.
- Structural edit evidence followed by the existing human approval/export gate.
- Mock Provider proves orchestration only; real edit quality needs a configured real model and benchmark assets.

## Delivery Tasks

1. Add edit project/revision/layer/evidence tables and migrations; test immutable branching and source validation.
2. Add mask normalization and deterministic composition services; test dilation, feathering, transforms, text, and Logo layers.
3. Add AI edit APIs and worker input routing; test exact source/mask ordering, capability checks, failure recovery, and evidence.
4. Add the editor, revision history, comparison UI, model capability filtering, and links from batch detail.
5. Add M4 Playwright coverage and `scripts/verify-m4.sh`; update README/spec, verify feature branch and merged `main`.

## Release Boundaries

- Automated evidence proves source/mask provenance, output decodability, dimensions, and requested operation. It does not prove semantic edit quality.
- Text and Logo content are deterministic layers; generated decorative text is never treated as authoritative product copy.
- M5 platform expansion, bulk import, cost reporting, local ComfyUI/GPU scheduling, and publishing remain out of scope.
