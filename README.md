# mutable-default

Detect mutable default argument values in Python source code.

`mutable-default` scans Python files for function parameters whose default value is a
mutable literal (list, dict, set) or a mutable constructor call (`list()`, `dict()`,
`set()`). Such defaults are evaluated once at function-definition time and shared
across calls, a classic source of subtle bugs.

## Features

- AST-based detection (no false positives from comments or strings).
- Covers regular functions, async functions, methods, and lambdas.
- Handles positional and keyword-only parameters.
- Prunes common build/dependency/cache directories.
- Text and JSON output; non-zero exit code for CI gating.
- Zero runtime dependencies (Python standard library only).

## Install

No external dependencies are required. Python 3.9 or newer is recommended.

```sh
git clone https://github.com/example/mutable-default.git
cd mutable-default
```

Run directly:

```sh
python -m mutable_default .
```

## Usage

Scan the current directory:

```sh
python -m mutable_default .
```

Scan another project:

```sh
python -m mutable_default /path/to/project
```

Emit JSON:

```sh
python -m mutable_default /path/to/project --format json
```

Exclude directories:

```sh
python -m mutable_default . --exclude tests --exclude vendor
```

Sample output:

```
src/foo.py:12: build() param 'items' has mutable default (list)
src/foo.py:20: handler() param 'cache' has mutable default (dict)

Found 2 mutable default argument(s).
```

## License

MIT
