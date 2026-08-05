# Documentation

Build the Sphinx documentation locally with Poetry:

```bash
poetry install --with docs
poetry run sphinx-build -W -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` after the build completes.
