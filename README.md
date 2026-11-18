# Code Comment Generator - AST + NLP

An AST-driven Python documentation system that analyzes Python source code and generates Google-style docstrings and inline comments. It combines deterministic compiler analysis, T5-based natural-language generation, and optional confidence-gated neurosymbolic and LLM-assisted review.

## What It Does

The pipeline can:

- parse and validate Python source;
- extract functions, classes, parameters, imports, calls, returns, and exceptions;
- calculate cyclomatic complexity and build semantic context;
- generate docstrings and inline comments;
- lower functions into IR and inspect CFG/DFA patterns;
- detect common security risks before modifying source;
- display AST and analysis results in a PyQt6 desktop application;
- optionally fine-tune T5-small on structured AST features.

## Generation Engines

| Engine | CLI flag | Behavior |
|---|---|---|
| Rule-based | default | Deterministic AST analysis, with no trained model required |
| AST+NLP ML | `--ml` | Uses T5-small to write the summary, while preserving AST-derived Args, Returns, and Raises sections |
| Neurosymbolic | `--neurosymbolic` | Combines the ML summary with symbolic AST evidence and consistency checks |
| Optional LLM review | `--agent-review` | Revises only docstring summary lines through an OpenAI-compatible endpoint |

ML and neurosymbolic modes require `outputs/model/ast_model/`. At present, this repository includes generated datasets and reports but no saved T5 model, so train a model before selecting those modes.

## Project Layout

```text
.
├── src/
│   ├── main.py                 # CLI entry point and pipeline
│   ├── parser_module.py        # Source reading and ast.parse wrapper
│   ├── validator.py            # AST validation
│   ├── ast_extractor.py        # AST feature extraction
│   ├── ast_body_extractor.py   # Function-body, return, and raise extraction
│   ├── context_analyzer.py     # Semantic context and complexity analysis
│   ├── comment_generator.py    # Rule-based and ML comment generation
│   ├── comment_attacher.py     # Inserts comments and docstrings
│   ├── llm_review_agent.py     # Optional OpenAI-compatible summary review
│   ├── security_analyzer.py    # Security pattern analysis and safety gate
│   ├── logger.py               # Pipeline JSON/text logging
│   ├── ml/                     # Dataset, T5 model, trainer, and evaluator
│   ├── ir/                     # Intermediate representation
│   ├── analysis/               # CFG, DFA, and code-pattern analysis
│   ├── neurosymbolic/          # Confidence-gated ML/symbolic fusion
│   └── gui/                    # PyQt6 desktop application
├── tests/
│   ├── inputs/                 # CLI and security test samples
│   ├── test_*.py               # unittest and pytest test modules
│   ├── logs/                   # Generated pipeline logs
│   └── outputs/                # Generated test artifacts
├── outputs/
│   ├── ast_train_dataset.json  # Saved training corpus
│   ├── ast_train_dataset.csv   # Training corpus in CSV form
│   ├── training_report.json    # Dataset and training metadata
│   └── eval_report.json        # Evaluation metrics
├── web/index.html              # Standalone browser demo
├── tools/
│   ├── generate_architecture_png.py
│   └── generate_architecture_pdf.py
├── run_gui.py                  # PyQt6 GUI entry point
├── walkthrough.md              # Architecture and implementation walkthrough
├── guide.md                    # Feature-by-feature guide
└── walkthroughui.md            # GUI-specific walkthrough
```

## Requirements

- Windows or another environment with Python 3.10 or later
- Core AST, IR, security, and rule-based generation: Python standard library
- ML training and generation: NumPy, PyTorch, Transformers, and usually SentencePiece
- CodeSearchNet training: Hugging Face `datasets`
- Desktop GUI: PyQt6
- Evaluation/chart panels: Matplotlib
- Tests: pytest for the optional T5 test module

The repository does not currently include `requirements.txt`, `pyproject.toml`, or a Conda environment file. Install the needed feature set explicitly.

### Core and GUI setup

```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install numpy torch transformers datasets sentencepiece PyQt6 matplotlib pytest
```

For a CUDA build, install the PyTorch build recommended for your GPU and driver instead of relying on the default CPU package.

## Quick Start

Run commands from the repository root.

### Rule-based generation

Analyze a sample:

```powershell
python -m src.main tests\inputs\complex_sample.py
```

Write annotated source to a file:

```powershell
python -m src.main tests\inputs\complex_sample.py --output generated_complex.py
```

### Train the T5 model

Smoke-test training:

```powershell
python -m src.main --train `
  --epochs 1 `
  --batch-size 2 `
  --codesearchnet-max 20 `
  --max-stdlib-files 10
```

A medium local/GPU-oriented run:

```powershell
python -m src.main --train `
  --codesearchnet-max 8000 `
  --max-stdlib-files 600 `
  --epochs 3 `
  --batch-size 8 `
  --grad-accum-steps 1
```

Training combines Hugging Face CodeSearchNet when available with Python standard-library source as a fallback or supplement.

### ML and neurosymbolic generation

After training succeeds and `outputs/model/ast_model/` exists:

```powershell
python -m src.main tests\inputs\complex_sample.py --ml
python -m src.main tests\inputs\complex_sample.py --neurosymbolic
```

If the model is missing, the CLI prints instructions and exits with status 2 rather than silently falling back.

### Desktop GUI

```powershell
python run_gui.py
```

The GUI contains Generator, Insights, ML Training, Security, and Logs workspaces. The Insights workspace visualizes AST features, context/call graphs, IR, pattern findings, evaluation charts, and security results.

### Standalone web demo

Open `web/index.html` directly, or serve the repository locally:

```powershell
python -m http.server 8000
```

Then visit `http://localhost:8000/web/index.html`. This demo has no Python backend or API dependency.

## CLI Reference

```text
python -m src.main [file.py] [options]
```

### Pipeline options

| Option | Description |
|---|---|
| `file.py` | Python source file to analyze |
| `-o FILE`, `--output FILE` | Write annotated source to a file |
| `--logs` | Save pipeline JSON/text logs and `analysis_report.json` |
| `--show-features` | Print extracted AST features as JSON |
| `--show-context` | Print the semantic context graph as JSON |
| `--ir` | Print the lowered intermediate representation |
| `--analysis` | Print CFG/DFA-based code-pattern findings |
| `--ml` | Require AST+NLP T5 generation |
| `--neurosymbolic` | Use confidence-gated ML plus symbolic evidence |
| `--agent-review` | Review docstring summary lines with an OpenAI-compatible LLM |
| `--train` | Build the dataset, train/evaluate the model, and exit |

### Training options

| Option | Default | Description |
|---|---:|---|
| `--epochs` | `4` | Fine-tuning epochs |
| `--batch-size` | `8` | Training batch size |
| `--grad-accum-steps` | `1` | Gradient accumulation steps |
| `--lr` | `2e-4` | Learning rate |
| `--codesearchnet-max` | `20000` | Maximum CodeSearchNet samples |
| `--max-stdlib-files` | `1500` | Maximum standard-library source files |
| `--no-codesearchnet` | disabled | Skip CodeSearchNet |
| `--no-stdlib` | disabled | Skip the stdlib fallback/supplement |
| `--output-dir DIR` | `outputs` | Model and report destination |
| `--block-max-pairs` | `20000` | Maximum block-level inline-comment training pairs |

Relative `--output-dir` paths are resolved against the repository root.
`--block-max-pairs` is currently accepted by the CLI but is not yet passed into the training dataset builder.

## Optional LLM Review

LLM review is opt-in. It is disabled for normal rule-based, ML, and neurosymbolic runs unless `--agent-review` is supplied.

Local Ollama-compatible endpoint example:

```powershell
$env:COMMENT_AGENT_BASE_URL="http://localhost:11434/v1"
$env:COMMENT_AGENT_MODEL="llama3.1"
python -m src.main tests\inputs\complex_sample.py --agent-review
```

Authenticated OpenAI-compatible endpoint example:

```powershell
$env:COMMENT_AGENT_BASE_URL="https://your-endpoint.example/v1"
$env:COMMENT_AGENT_MODEL="your-model"
$env:COMMENT_AGENT_API_KEY="your-api-key"
python -m src.main tests\inputs\complex_sample.py --agent-review
```

| Variable | Default | Purpose |
|---|---|---|
| `COMMENT_AGENT_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible API base URL |
| `COMMENT_AGENT_MODEL` | `llama3.1` | Model name |
| `COMMENT_AGENT_API_KEY` | unset | Optional bearer token |

The reviewer receives source snippets and existing summaries. It may replace only the summary sentence; parameter, return, exception, and security sections remain AST-derived.

## Training and Output Artifacts

Successful training writes artifacts under `outputs/`:

- `outputs/model/ast_model/` - trained T5 model and tokenizer
- `outputs/ast_train_dataset.json` - saved AST/NLP pairs
- `outputs/ast_train_dataset.csv` - dataset in CSV form
- `outputs/training_report.json` - dataset and training metadata
- `outputs/eval_report.json` - BLEU-4, ROUGE-L, exact-match results

The training report records the data contract:

- `data_profile.input_mode = "AST structured features"`
- `data_profile.target_mode = "NLP docstring sentence"`
- `data_profile.ast_nlp_pairs`

The current checked-in reports show that training data was built, but the T5 fine-tuning step was skipped because Transformers/Torch were unavailable or the model was not saved.

## Security Gate

The pipeline always performs static security analysis before generation or source attachment. It detects patterns including:

- `eval`, `exec`, and `compile`;
- shell-enabled subprocess calls;
- hardcoded passwords, secrets, and tokens;
- weak cryptographic functions;
- SQL string concatenation;
- bare `except` clauses;
- mutable default arguments;
- assertions outside tests;
- unsafe pickle/YAML deserialization;
- insecure randomness;
- hardcoded network locations.

Generation is aborted when:

- a critical issue is found; or
- the module safety score is below 80%.

The per-function score starts at 100 and deducts 30 for critical, 15 for high, 5 for medium, and 1 for low findings. Module safety is the percentage of functions with a score of at least 80.

This gate is a static-analysis safeguard, not a complete security audit.

## Docstring Safety

Before source insertion, generated docstrings:

- escape triple quotes that could terminate a docstring;
- avoid invalid raw-string prefixes;
- validate parameter, type, return, and exception text;
- preserve the generated Python syntax.

Generated source is parsed again before the pipeline reports success.

## Testing

Run the standard unittest discovery suite:

```powershell
python -m unittest discover -s tests -v
```

Run the pytest suite, including the optional T5 model tests:

```powershell
python -m pytest tests -q
```

Run focused modules:

```powershell
python -m unittest tests.test_basic -v
python -m unittest tests.test_security_agent -v
python -m unittest tests.test_llm_review_agent -v
```

The tests cover parsing, validation, AST extraction, comments, IR, CFG/DFA analysis, security, ML behavior, and optional LLM review.

## Pipeline

```text
Source
  -> Read and parse
  -> Validate AST
  -> Extract AST features
  -> Analyze semantic context
  -> Run security gate
  -> Generate comments (rule / ML / neurosymbolic)
  -> Optional LLM summary review
  -> Attach comments/docstrings
  -> Build IR
  -> Build CFG
  -> Run DFA
  -> Detect code patterns
  -> Write source and reports
```

## Architecture References

- [Implementation walkthrough](walkthrough.md)
- [Feature guide](guide.md)
- [GUI walkthrough](walkthroughui.md)

## License

This project is licensed under the terms in [LICENSE](LICENSE).
