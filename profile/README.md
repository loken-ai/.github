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

Being split out of a single working tree — the names below are where each piece is headed,
and they will become links as the repositories land.

| Repo | What it is |
|------|------------|
| **loken** | The inference **server** — engine, tensor substrate, all modalities, OpenAI/Ollama-compatible API |
| **loken-verve** | **verve** — a local-first terminal coding agent |
| **loken-gui** | Desktop **GUI client** for any Ollama/OpenAI-compatible server |
| **loken-bench** | Benchmarks one local inference server against another, on the same prompts and the same clock |
| **loken-cudarc** | Transitional CUDA-driver fork (goal: upstream and retire) |

## Status

🧪 **Experimental.** APIs and internals move fast. Model *weights* are never distributed here —
each model remains under its own license and terms.

## Acknowledgements

None of this would exist without the projects that mapped the territory first.

| Project | What LOKEN owes it |
|---------|--------------------|
| [**ggml**](https://github.com/ggml-org/ggml) | The quantisation block formats it dequantises — the k-quants above all — and **GGUF**, the container it reads |
| [**llama.cpp**](https://github.com/ggml-org/llama.cpp) | Building those into an engine, and proving quantised local inference was practical |
| [**Ollama**](https://github.com/ollama/ollama) | The API and the model-management ergonomics it stays compatible with |
| [**vLLM**](https://github.com/vllm-project/vllm) | Continuous batching and paged attention — the ideas behind the concurrent decode path |
| [**candle**](https://github.com/huggingface/candle) | Being where this project started: a Rust tensor library with real CUDA support, which is what made a full-Rust engine plausible at all |

Three of them are also the yardstick. Performance claims here come from runs against
llama.cpp, Ollama and vLLM — same prompts, same clock — and the cases where LOKEN loses are
published with the rest.

### Why LOKEN no longer builds on candle

Not because anything is wrong with it. The two projects simply want different things: candle is
a general-purpose tensor library, and a general-purpose op is the right default right up until
you start measuring yourself against vLLM.

The break came out of profiling rather than principle. Two examples, both in the sampler:

- **Batched greedy decode.** candle's `argmax`, plus the per-row host scan around it, cost
  roughly 2 ms per step at batch 8. That one generic op accounted for essentially the whole of
  the throughput gap against vLLM at that batch size; a native kernel closed most of it.
- **The sampled path.** Per-row softmax, sort and multinomial were running on the device, once
  per row, per step.

Every one of those fixes meant owning the kernel outright — and past a certain number of them,
the generic layer underneath is no longer carrying anything.

So LOKEN runs on its own tensor substrate, and candle's source stays what it has always been
here: a reference worth reading.

## License

Dual-licensed **MIT OR Apache-2.0**, at your option. Third-party attributions are listed in each
repo's `NOTICE.md`.
