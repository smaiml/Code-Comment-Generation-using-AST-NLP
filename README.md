# Code Comment Generator - AST + NLP

An AST-driven Python documentation system that analyzes source code and generates Google-style docstrings and inline comments. It combines deterministic compiler-analysis techniques with T5-based natural-language generation and an optional OpenAI-compatible LLM review.

## Features

- **Three generation engines**
  - Rule-based AST generation
  - AST+NLP T5 generation
  - Neurosymbolic confidence-gated fusion of ML and symbolic rules
- **AST and semantic analysis**
  - Function, class, import, parameter, return, and exception extraction
  - Cyclomatic complexity and variable/type/context analysis
  - Intermediate representation and control-flow graph generation
  - Reaching-definitions, live-variable, and code-pattern analysis
- **Security analysis**
  - Detects unsafe built-ins, weak cryptography, shell/SQL injection risks, secrets, insecure deserialization, and other vulnerable patterns
  - Stops generation when a critical issue or a module safety score below 80% is detected
- **PyQt6 desktop GUI**
  - Generator, ML training, insights, security, and pipeline-log workspaces
- **Optional LLM review**
  - Revises only the one-line docstring summary through an OpenAI-compatible chat endpoint
- **Standalone web demo**
  - No backend or API required

## Project Layout

```text
.
├── src/
│   ├── main.py                 # CLI entry point and pipeline
│   ├── parser_module.py        # Source reading and ast.parse wrapper
│   ├── ast_extractor.py        # AST feature extraction
│   ├── context_analyzer.py     # Semantic context analysis
│   ├── comment_generator.py    # Rule-based and ML comment generation
│   ├── comment_attacher.py     # Inserts generated comments into source
│   ├── llm_review_agent.py     # Optional OpenAI-compatible review
│   ├── security_analyzer.py    # Security vulnerability gate
│   ├── logger.py               # Pipeline JSON/text logging
│   ├── ml/                     # Dataset, T5 model, trainer, evaluator
│   ├── ir/                     # Intermediate representation
│   ├── analysis/               # CFG, DFA, and pattern detection
│   ├── neurosymbolic/          # Confidence-gated fusion engine
│   └── gui/                    # PyQt6 desktop interface
├── tests/
│   ├── inputs/                 # Example Python inputs
│   ├── test_*.py               # Unit tests
│   └── outputs/                # Test/generated artifacts
├── web/
│   └── index.html              # Standalone interactive visualization
├── outputs/                    # Training reports and saved models
├── run_gui.py                  # Desktop GUI entry point
└── DOCUMENTATION.md            # Detailed project documentation
```

## Requirements

Recommended:

- Python 3.10 or later
- PyTorch and Transformers for AST+NLP training and ML generation
- NumPy
- Hugging Face `datasets` for CodeSearchNet training data
- PyQt6 for the desktop GUI
- Internet access for downloading model and dataset assets, unless all assets are already available locally

The core rule-based, AST, IR, analysis, and security pipelines use the Python standard library. The project does not currently include a dependency manifest, so install optional packages explicitly.

```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install numpy torch transformers datasets PyQt6
```

For a CPU-only PyTorch installation, use the appropriate command from the official PyTorch instructions for your platform. CUDA can reduce T5 training time when compatible PyTorch/CUDA builds are used.

## Quick Start

From the repository root:

### 1. Rule-based generation

```powershell
python -m src.main tests\inputs\complex_sample.py
```

Write the annotated source to a file:

```powershell
python -m src.main tests\inputs\complex_sample.py --output generated_complex.py
```

### 2. Train the T5 model

```powershell
python -m src.main --train
```

A small smoke-test training run:

```powershell
python -m src.main --train `
  --epochs 1 `
  --batch-size 2 `
  --codesearchnet-max 20 `
  --max-stdlib-files 10
```

A medium GPU-oriented run:

```powershell
python -m src.main --train `
  --codesearchnet-max 8000 `
  --max-stdlib-files 600 `
  --epochs 3 `
  --batch-size 8 `
  --grad-accum-steps 1
```

Training uses Hugging Face CodeSearchNet when available and supplements or falls back to Python standard-library source files.

### 3. AST+NLP generation

```powershell
python -m src.main tests\inputs\complex_sample.py --ml
```

ML and neurosymbolic modes require a trained model under `outputs/model/ast_model/`. Generation exits with an error if the model is missing.

### 4. Neurosymbolic generation

```powershell
python -m src.main tests\inputs\complex_sample.py --neurosymbolic
```

The neurosymbolic engine combines T5 output with symbolic AST evidence and falls back to symbolic generation when confidence or consistency checks do not pass.

### 5. Launch the desktop GUI

```powershell
python run_gui.py
```

The GUI provides:

- Source-code editing and file loading
- Rule-based, ML, and neurosymbolic generation
- Optional LLM summary review
- AST, context, CFG/IR, evaluation, and security visualizations
- Training controls and pipeline logs

### 6. Open the web demo

Open [`web/index.html`](web/index.html) directly in a browser, or run a temporary static server:

```powershell
python -m http.server 8000
```

Then visit `http://localhost:8000/web/index.html`.

The web demo is independent of the Python backend. It demonstrates editable examples, simulated generation, pipeline progress, comment-only output, and copy controls.

## CLI Reference

```text
python -m src.main [file.py] [options]
```

| Option | Description |
|---|---|
| `file.py` | Python source file to analyze |
| `-o FILE`, `--output FILE` | Write annotated source to a file |
| `--logs` | Save JSON/text pipeline logs and an analysis report |
| `--show-features` | Print extracted AST features as JSON |
| `--show-context` | Print the semantic context graph as JSON |
| `--ir` | Print the intermediate-representation dump |
| `--analysis` | Print code-pattern analysis findings |
| `--ml` | Require AST+NLP T5 generation |
| `--neurosymbolic` | Use confidence-gated ML + symbolic generation |
| `--agent-review` | Review one-line docstring summaries with an LLM |
| `--train` | Train the AST+NLP model and exit |

Training options:

| Option | Default | Description |
|---|---:|---|
| `--epochs` | `4` | Fine-tuning epochs |
| `--batch-size` | `8` | Training batch size |
| `--grad-accum-steps` | `1` | Gradient accumulation steps |
| `--lr` | `2e-4` | Learning rate |
| `--codesearchnet-max` | `20000` | Maximum CodeSearchNet samples |
| `--max-stdlib-files` | `1500` | Maximum standard-library files |
| `--no-codesearchnet` | Disabled | Skip the CodeSearchNet source |
| `--no-stdlib` | Disabled | Skip the standard-library fallback |
| `--output-dir DIR` | `outputs` | Model and report destination |

## Optional LLM Review

LLM review is opt-in and is not used by normal rule-based, ML, or neurosymbolic runs.

```powershell
$env:COMMENT_AGENT_BASE_URL="http://localhost:11434/v1"
$env:COMMENT_AGENT_MODEL="llama3.1"
python -m src.main tests\inputs\complex_sample.py --agent-review
```

For an OpenAI-compatible service that requires authentication:

```powershell
$env:COMMENT_AGENT_BASE_URL="https://your-endpoint.example/v1"
$env:COMMENT_AGENT_MODEL="your-model"
$env:COMMENT_AGENT_API_KEY="your-api-key"
python -m src.main tests\inputs\complex_sample.py --agent-review
```

Environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `COMMENT_AGENT_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible API base URL |
| `COMMENT_AGENT_MODEL` | `llama3.1` | Model name |
| `COMMENT_AGENT_API_KEY` | unset | Optional bearer token |

The reviewer receives source snippets and generated summaries. It may revise only the summary line; parameter, return, and exception sections generated from AST remain unchanged.

## Output Artifacts

After CLI training, artifacts are saved under `outputs/`:

- `outputs/model/ast_model/` - trained T5 model and tokenizer
- `outputs/ast_train_dataset.json` - saved AST/NLP pairs
- `outputs/ast_train_dataset.csv` - dataset in CSV format
- `outputs/training_report.json` - dataset and training metadata
- `outputs/eval_report.json` - BLEU-4, ROUGE-L, and exact-match results

The training report records:

- `data_profile.input_mode = "AST structured features"`
- `data_profile.target_mode = "NLP docstring sentence"`
- `data_profile.ast_nlp_pairs`

During CLI runs with `--logs`, the pipeline writes logs beside the input file's parent `logs/` directory and saves the static analysis report under `outputs/analysis_report.json`.

## Docstring Safety

Both generation engines sanitize dynamic docstring content before source insertion:

- Escapes triple quotes that could terminate a docstring
- Removes invalid raw-string prefixes
- Validates parameter, type, return, and exception text
- Preserves valid Python syntax for generated output

The result can then be parsed as Python source by the CLI pipeline.

## Security Gate

Before comments are generated or attached, the source is scanned for security issues. Generation is aborted if:

- A critical issue is found, or
- The module safety score is below 80%.

This gate is a static-analysis safeguard, not a complete security audit.

## Testing

Run the test suite:

```powershell
python -m unittest discover -s tests -v
```

Run a focused test module:

```powershell
python -m unittest tests.test_basic -v
python -m unittest tests.test_security_agent -v
python -m unittest tests.test_llm_review_agent -v
```

The test suite covers parsing, validation, AST extraction, comments, IR, CFG/DFA analysis, security analysis, ML model behavior, and optional LLM review.

## Pipeline

```text
Source
  -> Parse
  -> Validate
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

See [`DOCUMENTATION.md`](DOCUMENTATION.md) for the detailed module, data structure, CLI, and architecture reference.

## License

This project is licensed under the terms in [`LICENSE`](LICENSE).
