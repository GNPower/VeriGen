# CLI Reference

```
verigen <command> [options]
```

Every command exits non-zero and prints a single clear message on a definition,
validation, extension, or generation error.

## generate

Render a definition into output files.

```bash
verigen generate <definition> -o <output_dir> [-c <values.yaml>] [--save-values]
```

- `-c, --config`: a values config. Omit it to use each variable's declared
  default (a notice is printed).
- `-o, --output`: the output directory (created if absent). Required.
- `--save-values`: also write the normalized values config next to the output, so
  the run can be reproduced.

## validate

Check a definition, and optionally a values config, without writing anything.

```bash
verigen validate <definition> [-c <values.yaml>]
```

## list

Discover and list generator definitions. A definition is any file named
`definition.yaml` or `*.verigen.yaml`.

```bash
verigen list                  # the built-in example generators
verigen list <path> [<path>]  # search the given files or directories
```

## new

Scaffold a starter generator directory (definition, a template, and an example
values config).

```bash
verigen new <id> [-o <parent_dir>]
```

## gui

Open the graphical interface. With no argument it shows a catalog of the built-in
examples; with a definition it opens that generator's wizard. Requires the `gui`
extra. By default it opens in a native desktop window (pywebview ships with the
extra); `--web` uses the browser instead.

```bash
verigen gui                   # catalog, native window
verigen gui <definition>      # one generator
verigen gui --web             # use the browser
verigen gui --port 9000       # choose the HTTP port
```

## schema

Print the generator-definition format as JSON Schema, for editor autocompletion
or CI validation.

```bash
verigen schema                # to stdout
verigen schema -o verigen.schema.json
```
