# AI Uzumchi Bot — Product Plan

## What this is

A Telegram bot for grape growers ("uzumchi"). A user sends a photo of a
grape leaf and the bot:

1. Predicts the **grape vine (variety) type** from the image.
2. Gives **detailed information about that variety and its yield**.
3. Predicts whether the leaf is **diseased or healthy**.
4. If diseased, gives **detailed information about the disease** and
   **how to treat it**.
5. If healthy, tells the user the leaf looks healthy.
6. Gives **additional info** — agrotechnics, harvest timing, spraying
   schedule, etc. — relevant to the detected variety/disease.
7. Lets the user **chat with an LLM** — by text or voice — for follow-up
   questions about any of the above.

This is currently the **MVP stage**. There is no paid/"Pro" tier — every
feature below is free while we validate the product and collect data.

### Client request vs. MVP simplification

The client's original ask (see product brief) was for every one of the
above — variety, disease, treatment, and agrotechnics info — to come
with **reference photos** (variety photos, disease photos, medicine/
treatment photos). Maintaining a curated, correctly-licensed image
library per variety/disease/treatment is a heavy lift for an MVP (sourcing,
tagging, storage, keeping it in sync as labels change) and isn't
something the classifier or dataset work gets us for free.

For MVP, we're dropping the *curated reference image* requirement and
instead having the **LLM (Gemini) generate the informational text**
(variety description, disease description, treatment steps, agrotech
notes) on demand, grounded in the classifier's output. No image
galleries to source or maintain — text-only responses from the LLM step.
If reference photos turn out to matter to users after launch, that's a
post-MVP addition (e.g. a small hand-picked image set per label), not a
blocker now.

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
| 1 | Vine type prediction | Leaf photo | Grape variety guess |
| 2 | Variety info | Predicted variety | LLM-generated text: description + yield info (no reference images) |
| 3 | Disease detection | Leaf photo | Healthy / Diseased |
| 4 | Disease classification | Leaf photo | Disease name (when diseased) |
| 5 | Disease + treatment info | Predicted disease | LLM-generated text: cause, treatment steps, prevention (no reference images) |
| 6 | Agrotech info | Predicted variety/disease | LLM-generated text: agrotechnics, harvest timing, spraying schedule |
| 7 | Diagnosis chat (text) | Free-text question, with the diagnosis as context | LLM answer: cause, treatment, prevention |
| 8 | Diagnosis chat (voice) | Voice message | Speech-to-text → LLM → text-to-speech reply (and/or text) |
| 9 | Dataset collection | Every submitted image | Stored (image + predictions + optional user feedback/correction) for future training |

Explicitly **out of scope for MVP**:
- Payments / subscription / "Pro" plan.
- Multi-model ensembles or model retraining pipeline automation.
- Anything beyond the single-image, single-turn-diagnosis-then-chat flow.
- Curated reference photo galleries (variety photos, disease photos,
  treatment/medicine photos) — replaced by LLM-generated text for MVP,
  see above.

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
Prediction(s) → LLM (Gemini): generate variety info, disease + treatment
info, agrotech notes — text only, no reference images
      │
      ▼
Bot replies with prediction summary + confidence + LLM-generated info
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
- **LLM layer** — a `utils/llm.py`-style wrapper around the Gemini API
  that takes the prediction result (variety, disease, healthy/diseased)
  and returns generated text: variety + yield info, disease + treatment
  info, and agrotech notes, plus conversation-history-aware answers for
  follow-up chat. One wrapper, two call shapes: an initial
  "generate info for this prediction" call right after classification,
  and a "continue the conversation" call for follow-ups. Keep all
  prompt/context construction here, not inline in handlers. No reference
  images are sourced or attached — everything here is generated text.
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
- Gemini is the working assumption for the LLM layer (text generation +
  chat) — confirm which Gemini model/tier, and whether it also handles
  voice natively or we still need separate TTS/STT.
- How do we keep LLM-generated variety/disease/treatment info accurate
  (hallucination risk) — fixed prompt templates per label with strong
  grounding instructions? Spot-check some outputs before shipping labels
  live.
- Where do collected images live (disk vs. object storage/S3-compatible)
  and what's the retention/consent story for user photos?
- How is "disease type" taxonomy defined initially (fixed label set vs.
  open-ended)?
