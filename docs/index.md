# pygleif

This library uses Python to query the [GLEIF.org](https://www.gleif.org/) API. It
supports fetching LEI records, searching by organisation identifiers, relationship
lookups, ISIN mappings and more. The library is strictly typed using
[Pydantic](https://github.com/pydantic/pydantic).

```{note}
This documentation covers the **v2** API (`pygleif.v2.GleifClient`). The legacy
`pygleif.v1` API (`PyGleif`, `Search`) is deprecated and not documented here.
```

## Installing the library

```
pip install pygleif
```

To install the latest in-development version from `main` (may be ahead of the
last PyPI release):

```
pip install git+https://github.com/ggravlingen/pygleif.git@main
```

```{toctree}
:maxdepth: 2
:hidden:

usage
api/index
```
