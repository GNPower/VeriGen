"""Optional Python extension for the extension_demo generator.

This file lives next to its definition and is loaded only because the definition
declares ``extension: ext.py``. It demonstrates the three hook kinds VeriGen
exposes. Domain logic like this stays in the author's repo, never in VeriGen.
"""


def register(api):
    @api.filter("shout")
    def _shout(value):
        """A trivial custom filter: uppercase and add emphasis."""
        return f"{str(value).upper()}!"

    @api.validator
    def _depth_is_power_of_two(values, definition):
        """Reject a depth that is not a power of two."""
        depth = values.get("depth", 0)
        if depth < 1 or (depth & (depth - 1)) != 0:
            return [f"depth ({depth}) must be a positive power of two"]
        return []

    @api.context
    def _derive_address_width(values, definition):
        """Provide a derived value the templates can use."""
        depth = values.get("depth", 1)
        addr_width = max(1, (depth - 1).bit_length())
        return {"addr_width": addr_width}
