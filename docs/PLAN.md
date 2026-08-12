# AI Uzumchi Bot — Product Plan

## What this is

A Telegram bot for grape growers ("uzumchi"). A user sends a photo of a
grape leaf and the bot:

1. Predicts whether the leaf is **diseased or healthy**.
2. If diseased, predicts the **disease type**.
3. Predicts the **grape vine (variety) type** from the image.
4. Lets the user **chat with an LLM** — by text or voice — about the
   diagnosis: what's wrong, why it happens, and how to treat/fix it.

This is currently the **MVP stage**. There is no paid/"Pro" tier — every
feature below is free while we validate the product and collect data.

## Why

Small/independent grape growers often can't get fast access to an
agronomist. A photo-in, diagnosis-and-advice-out bot lowers that barrier.
The image classifier will not be very accurate at first — a core MVP goal
is to **collect real user-submitted images** (with predictions and, where
possible, corrected labels) to build a proper training dataset for future
model versions.

## MVP feature scope

| # | Feature | Input | Output |
|---|---------|-------|--------|
| 1 | Disease detection | Leaf photo | Healthy / Diseased |
| 2 | Disease classification | Leaf photo | Disease name (when diseased) |
| 3 | Vine type prediction | Leaf photo | Grape variety guess |
| 4 | Diagnosis chat (text) | Free-text question, with the diagnosis as context | LLM answer: cause, treatment, prevention |
| 5 | Diagnosis chat (voice) | Voice message | Speech-to-text → LLM → text-to-speech reply (and/or text) |
| 6 | Dataset collection | Every submitted image | Stored (image + predictions + optional user feedback/correction) for future training |

Explicitly **out of scope for MVP**:
- Payments / subscription / "Pro" plan.
- Multi-model ensembles or model retraining pipeline automation.
- Anything beyond the single-image, single-turn-diagnosis-then-chat flow.

## Rough flow

```
User sends photo
      │
      ▼
Save image (+ metadata) ──► dataset store
      │
      ▼
Run classifier(s): disease? disease type? vine type?
      │
      ▼
Bot replies with prediction summary + confidence
      │
      ▼
User asks follow-up (text or voice)
      │
      ▼
Voice → STT (if voice)                     ─┐
Prediction context + conversation → LLM     ├─► LLM answer
LLM answer → TTS (if user used voice)      ─┘
      │
      ▼
Bot replies (text and/or voice)
```

## Architecture notes (how this maps onto the existing codebase)

The bot is already built on `aiogram 3` + `SQLAlchemy 2.0 (async)` +
`alembic` (see [`CLAUDE.md`](../CLAUDE.md) for the current architecture).
To build the above we expect to add, without restructuring what exists:

- **New handler group** `handlers/diagnosis/` — receives photo/voice
  messages, orchestrates classification + LLM chat. Same
  `Router(name=__name__)` convention as `handlers/register/`,
  `handlers/admin/`, etc.
- **New DB models** under `db/models/` — something like `Submission`
  (image file id/path, uploader, timestamps), `Prediction` (disease
  label, vine type label, confidences, model version), and a matching
  repository under `db/repositories/` following the existing
  `UserRepository` pattern (methods take `session: AsyncSession` as the
  first argument, no session management inside the repo).
- **Inference layer** — a thin wrapper in `utils/` (or a dedicated
  `ml/` package if it grows) that loads the classifier(s) and exposes an
  async-friendly `predict(image_bytes) -> PredictionResult` call. Model
  choice/training is a separate track — start with whatever off-the-shelf
  or lightly fine-tuned model gets a v1 shipped, since accuracy improves
  once real user data is collected.
- **LLM layer** — a `utils/llm.py`-style wrapper that takes the
  prediction result + conversation history and returns an answer. Keep
  the prompt/context construction here, not inline in handlers.
- **Voice** — speech-to-text on incoming voice messages, text-to-speech
  on outgoing LLM replies when the user is talking by voice. Keep both
  behind small helper functions so the LLM layer doesn't need to know
  whether the turn was text or voice.
- **Dataset storage** — every submitted image gets persisted (object
  storage or disk, path recorded in the DB) regardless of whether the
  user continues the chat. This is a first-class requirement, not an
  afterthought — it's the whole point of running MVP before a "Pro"
  plan.

## Open questions (resolve before/while building)

- Which model(s) for disease + vine-type classification, and where do
  they run (in-process vs. a separate inference service)?
- Which LLM provider, and does it need to support voice output natively
  or do we handle TTS/STT separately?
- Where do collected images live (disk vs. object storage/S3-compatible)
  and what's the retention/consent story for user photos?
- How is "disease type" taxonomy defined initially (fixed label set vs.
  open-ended)?
