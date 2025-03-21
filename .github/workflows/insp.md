name: Build

on:
  release:
    types: [published]
  push:
    branches:
      - main
      - ci
  pull_request:
    branches:
      - "*"

env:
  PROJECT_NAME: future

jobs:
    
  build:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
      - uses: actions/checkout@v1
        with:
          fetch-depth: 2
          submodules: false

      - name: Use Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e .
          pip install isort flake8 black pytest pytest-cov

      - name: Run tests
        run: |
          pytest --doctest-modules --junitxml=junit/pytest-results-${{ matrix.python-version }}.xml --cov=$PROJECT_NAME --cov-report=xml tests/

      - name: Run linters
        run: |
          echo "Running linters"

          pip install black
          flake8 .
          isort --check-only . 2>&1
          black --check . 2>&1

      - name: Upload pytest test results
        uses: actions/upload-artifact@master
        with:
          name: pytest-results-${{ matrix.python-version }}
          path: junit/pytest-results-${{ matrix.python-version }}.xml
        if: always()

      - name: Codecov
        run: |
          bash <(curl -s https://codecov.io/bash)

      - name: Install distribution dependencies
        run: |
          rm -rf junit
          rm -rf deps
          pip install build
        if: matrix.python-version == 3.11

      - name: Create distribution package
        run: python -m build
        if: matrix.python-version == 3.11

      - name: Upload distribution package
        uses: actions/upload-artifact@master
        with:
          name: dist
          path: dist
        if: matrix.python-version == 3.11

        
  publish:
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'release'
    steps:
      - name: Download a distribution artifact
        uses: actions/download-artifact@v2
        with:
          name: dist
          path: dist

      - name: Use Python 3.11
        uses: actions/setup-python@v1
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install twine

      - name: Publish distribution 📦 to Test PyPI
        run: |
          twine upload -r testpypi dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.test_pypi_password }}

      - name: Publish distribution 📦 to PyPI
        run: |
          twine upload -r pypi dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.pypi_password }}
