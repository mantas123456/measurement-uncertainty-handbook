# Measurement Uncertainty Handbook

A free, practical guide to method validation and measurement uncertainty for
ISO/IEC 17025 testing laboratories, with runnable Python notebooks on synthetic data.

**Site:** https://mantas123456.github.io/measurement-uncertainty-handbook/ (not live yet)

Calculations come from [`labqc`](https://github.com/mantas123456/lab-quality-toolkit)
([PyPI](https://pypi.org/project/labqc/)); this repository holds only text, notebooks and data.

## Layout

| Path | Contents |
| --- | --- |
| `docs/` | Chapter pages (Markdown), 01-foundations to 06-tools |
| `notebooks/` | One notebook per topic, rendered into the site by `hooks/notebooks.py` |
| `data/synthetic/` | CSVs written by `scripts/make_data.py` |
| `scripts/make_data.py` | Seeded generator; every assumption is documented in its comments |
| `overrides/` | GoatCounter analytics snippet |

## Build locally (Python 3.11)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/make_data.py          # regenerate the synthetic data
jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
mkdocs serve
```

CI (`.github/workflows/deploy.yml`) checks the data are up to date, executes every
notebook (any error fails the build), builds the site with `--strict` and deploys
it to GitHub Pages from `main`.

## Data

All data are synthetic. No real laboratory, client or employer data are used,
even anonymised.

## Licence

Text (`docs/`): [CC BY 4.0](LICENSE-docs). Code, notebooks and scripts: [MIT](LICENSE).
Cite with [`CITATION.cff`](CITATION.cff).
