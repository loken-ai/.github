<!--
  ORG PROFILE — rendered at https://github.com/loken-ai
  Branding: the token chain (white circles, emerald top circle) on the indigo tile. Full brand kit + source SVGs live in
  this repo under brand/. The top circle is a logo device; in text write "LOKEN".
-->

<p align="center">
  <img src="lockup.png" alt="LOKEN — Local · Multimodal · Green" width="480">
</p>

<p align="center">
  A full-Rust inference stack that runs large language <em>and</em> generative-media models
  entirely on your own machine.
</p>

---

## What is LOKEN?

**LOKEN** — from **Lo**cal + tok**en** — is a local-first, multimodal AI
stack written from the ground up in Rust: no Python at runtime, no heavyweight framework. One
server speaks the **OpenAI- and Ollama-compatible** APIs and covers many modalities:

- **Text** — chat/completions, embeddings, reranking
- **Vision** — image understanding (VLMs)
- **Speech** — text-to-speech and transcription
- **Generative media** — image, audio/music, video, and symbolic MIDI

It is built to be **private** — it runs on your hardware and calls nothing out — **efficient**,
with heterogeneous CPU/GPU placement and an eye on joules per token as much as tokens per
second, and **measured**: every performance claim comes from a run against llama.cpp, Ollama or
vLLM on the same prompts and the same clock, and the cases where it loses are published with
the rest.

## Repositories

| Repo | What it is |
|------|------------|
| [**loken**](https://github.com/loken-ai/loken) | The inference **server** — engine, tensor substrate, all modalities, OpenAI/Ollama-compatible API |
| [**loken-verve**](https://github.com/loken-ai/loken-verve) | **verve** — a local-first terminal coding agent |
| [**loken-gui**](https://github.com/loken-ai/loken-gui) | Desktop **GUI client** for any Ollama/OpenAI-compatible server |
| [**loken-bench**](https://github.com/loken-ai/loken-bench) | Benchmarks one local inference server against another, on the same prompts and the same clock |
| [**loken-cudarc**](https://github.com/loken-ai/loken-cudarc) | Transitional CUDA-driver fork (goal: upstream and retire) |

## Status

🧪 **Experimental.** APIs and internals move fast. Model *weights* are never distributed here —
each model remains under its own license and terms.

## License

Dual-licensed **MIT OR Apache-2.0**, at your option. Third-party attributions are listed in each
repo's `NOTICE.md`.
