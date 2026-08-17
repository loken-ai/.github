# Contributing to LOKEN

Thanks for your interest in contributing! These guidelines apply across the
[`loken-ai`](https://github.com/loken-ai) organization; individual repositories
may add their own specifics in a local `CONTRIBUTING.md`.

## Before you start

- For anything non-trivial, **open an issue first** to discuss the approach
  before writing code. This avoids wasted work on changes we can't merge.

## Development

The stack is **pure Rust**. To build and check a repo:

```bash
cargo build --release
cargo test
cargo fmt --all
cargo clippy --all-targets
```

Please make sure `fmt` and `clippy` are clean and tests pass before opening a PR.

## Project conventions

- **Full Rust, minimal dependencies.** Runtime is Rust-only (no Python). Adding a
  new crate dependency is a deliberate decision — **discuss it in an issue first**;
  many things are implemented in-tree on purpose.
- **Measure performance claims.** Any "this is faster/greener" change should come
  with a before/after measurement, not an estimate.
- **Respect licensing.** If you port or adapt third-party code, it must be under a
  permissive license (MIT / Apache-2.0 / BSD), you must keep the upstream
  attribution, and you must add an entry to that repo's `NOTICE.md`. Do not paste
  code from GPL/AGPL/non-commercial sources.
- **No secrets or machine-specific paths** in committed code — resolve paths via
  configuration.

## Pull requests

- Keep PRs focused and reasonably small; link the issue they address.
- Write clear commit messages explaining the *why*.
- Ensure CI is green.

## Licensing of contributions

Unless stated otherwise, contributions are accepted under the project's dual
license, **MIT OR Apache-2.0**. By submitting a contribution you agree that it
may be distributed under those terms.
