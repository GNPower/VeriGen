# VeriGen

VeriGen is a general, config-driven generator for Verilog and SystemVerilog. You
describe a module once as a *generator definition*, and VeriGen renders Jinja2
templates from that definition and a set of values.

VeriGen ships no IP-specific logic. Registers, FIFOs, bus bridges, and the like
are authored by you as templates plus config in your own repository, VeriGen justs
loads and renders them.

## Two kinds of file

- A **generator definition** (authored once): one YAML file declaring the
  metadata, the input variables grouped into wizard pages, the output templates,
  and an optional Python extension module. See [Authoring a Generator](authoring.md).
- A **values config** (per use): a plain `variable: value` mapping. The CLI reads
  one to generate headlessly; the wizard writes one when you save your inputs and
  reads one when you reload them. The same values file reproduces the same output
  through either interface.

## The pipeline

```
load definition -> validate values -> build context -> render templates -> write files
```

The CLI and the desktop wizard call this one path, so they produce identical
output from identical inputs.

## Next steps

- [Installation](installation.md)
- [Authoring a Generator](authoring.md)
- [Extension Hooks](extensions.md)
- [CLI Reference](cli.md)
