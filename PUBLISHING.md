# Publishing to PyPI

This guide explains how to publish the falkordb-orm package to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org/
2. **API Token**: Generate an API token from your PyPI account settings
3. **Poetry**: Ensure Poetry is installed (`pip install poetry`)

## Publishing Steps

### Option 1: Manual Publishing

1. **Build the package**:
   ```bash
   poetry build
   ```

2. **Verify the build**:
   ```bash
   ls dist/
   # Should show: falkordb_orm-1.0.0-py3-none-any.whl and falkordb_orm-1.0.0.tar.gz
   ```

3. **Test on TestPyPI first** (recommended):
   ```bash
   poetry config repositories.testpypi https://test.pypi.org/legacy/
   poetry config pypi-token.testpypi pypi-YOUR_TEST_TOKEN
   poetry publish -r testpypi
   ```

4. **Test installation from TestPyPI**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ falkordb-orm
   ```

5. **Publish to PyPI**:
   ```bash
   poetry config pypi-token.pypi pypi-YOUR_PYPI_TOKEN
   poetry publish
   ```

### Option 2: GitHub Actions (Recommended)

The repository includes a publish workflow that automatically publishes to PyPI when a GitHub release is created.

1. **Add PyPI token to GitHub Secrets**:
   - Go to repository Settings → Secrets and variables → Actions
   - Add a new secret named `PYPI_TOKEN` with your PyPI API token

2. **Create a GitHub Release**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   
   Then create a release from the tag on GitHub:
   - Go to Releases → Create a new release
   - Select the tag `v1.0.0`
   - Title: `v1.0.0 - Initial Release`
   - Description: Copy from CHANGELOG.md
   - Click "Publish release"

3. **Verify**: The GitHub Action will automatically build and publish to PyPI

## Post-Publishing

1. **Verify on PyPI**: Check https://pypi.org/project/falkordb-orm/

2. **Test installation**:
   ```bash
   pip install falkordb-orm
   ```

3. **Update README badge**: The PyPI badge should now show the correct version

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version: Incompatible API changes
- **MINOR** version: Add functionality (backwards-compatible)
- **PATCH** version: Bug fixes (backwards-compatible)

To release a new version:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with changes
3. Commit changes
4. Create a new tag and release

Example for patch release:
```bash
# Update pyproject.toml: version = "1.0.1"
# Update CHANGELOG.md
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 1.0.1"
git tag v1.0.1
git push origin main --tags
```

## Troubleshooting

### "Package already exists"
- The version is already published. Increment the version number.

### "Invalid credentials"
- Verify your API token is correctly configured
- Ensure the token has upload permissions

### "Package name taken"
- The package name `falkordb-orm` is reserved for this project

## Resources

- [Poetry Publishing Docs](https://python-poetry.org/docs/libraries/#publishing-to-pypi)
- [PyPI Help](https://pypi.org/help/)
- [TestPyPI](https://test.pypi.org/)
