# Reference: input attributes

`input_attributes` on a module declares the form the flow designer fills in on the builder page. The
list below is exhaustive — the builder renders these eleven types and no others, and each type's fields
are all the configuration it has. There is no way to add a custom control.

Import everything from `cw_addons.modules.models`. To see how these declarations turn into the
form a flow designer fills in, look at the annotated screenshot in
[chapter 4](../04-your-first-module.md).

## Fields every attribute has

| Field | Type | Required | |
|---|---|---|---|
| `name` | `str` | ✔ | The key. **Must match** the field name in your pydantic attributes model, or the value silently arrives empty. |
| `title` | `LangString` | ✔ | The field's label. |
| `description` | `LangString` | | Helper text under the field. Every type except `NameAttribute` has it, and each ships a placeholder default you should replace. |
| `required` | `bool` | | Defaults to `False`. |
| `type` | `str` | | Set by the class. Never pass it yourself. |

`LangString(en="…", cs="…")` — both languages are required.

## The eleven types

### `NameAttribute`

The node's own display name in the flow. Conventionally the first attribute.

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | Defaults to `"name"`; leave it. |
| `title` | `LangString` | |
| `required` | `bool` | |

No `description`, no default value.

```python
NameAttribute(name="name", title=LangString(en="Name", cs="Název"))
```

### `StringAttribute`

Single-line text input.

| Field | Type | Notes |
|---|---|---|
| `default_value` | `str \| None` | Prefills the field. |

```python
StringAttribute(
    name="greeting",
    title=LangString(en="Greeting", cs="Pozdrav"),
    description=LangString(en="Text sent to the customer.", cs="Text pro zákazníka."),
    default_value="Hello!",
    required=True,
)
```

### `TextAreaAttribute`

Multi-line text area. Same fields as `StringAttribute`.

| Field | Type | Notes |
|---|---|---|
| `default_value` | `str \| None` | |

Use it for prompts, templates, and anything a designer will paste a paragraph into. The pencil icon
beside the field opens a larger plain-text (Markdown) editor.

### `HtmlAttribute`

Rich text. Looks like `TextAreaAttribute`, but the pencil icon opens the builder's WYSIWYG editor —
the same one the native *Send email* node uses for its message body. Same fields as
`StringAttribute`.

| Field | Type | Notes |
|---|---|---|
| `default_value` | `str \| None` | HTML. |

Your attributes model receives an **HTML string**. Use it for email bodies and anything else that
ends up rendered as HTML.

```python
HtmlAttribute(
    name="body",
    title=LangString(en="Body", cs="Tělo"),
    description=LangString(en="Click the pencil to edit.", cs="Upravte kliknutím na tužku."),
    default_value="<p>Hello,</p>",
    required=True,
)
```

Worked example: `server/modules/catalog/email_draft.py`.

### `NumberAttribute`

Number input.

| Field | Type | Notes |
|---|---|---|
| `default_value` | `float \| None` | A float even when you mean an integer; cast in your module. |

```python
NumberAttribute(
    name="timeout_seconds",
    title=LangString(en="Timeout (seconds)", cs="Timeout (sekundy)"),
    description=LangString(en="How long to wait.", cs="Jak dlouho čekat."),
    default_value=5,
    required=True,
)
```

### `BooleanAttribute`

Checkbox.

| Field | Type | Notes |
|---|---|---|
| `default_value` | `bool \| None` | |

### `SelectAttribute`

Dropdown with a fixed set of options known at build time.

| Field | Type | Notes |
|---|---|---|
| `options` | `list[dict[str, str]]` | Single-entry `{value: label}` maps, in the order shown. |
| `default_value` | `str \| None` | **Must be one of the option values** — the model raises at import otherwise, so your addon fails to start. |
| `unique_in_list` | `bool` | Only inside a `ListAttribute`: each option may be picked in at most one row. Default `False`. |

```python
SelectAttribute(
    name="severity",
    title=LangString(en="Severity", cs="Závažnost"),
    description=LangString(en="How serious this is.", cs="Jak je to závažné."),
    options=[{"info": "Info"}, {"warning": "Warning"}, {"error": "Error"}],
    default_value="info",
    required=True,
)
```

### `StringListAttribute`

A chips input: the designer types a value and presses Enter, and it becomes a chip. The same control
the native *Send email* node uses for its recipients.

| Field | Type | Notes |
|---|---|---|
| `default_value` | `list[str] \| None` | |

Your attributes model receives a `list[str]`. Worked example: `server/modules/catalog/email_draft.py`.

### `ListAttribute`

A repeatable **group** of fields: one row per entry, several inputs per row.

| Field | Type | Notes |
|---|---|---|
| `attributes` | `list[...]` | The fields in one row. Required. |

Nested entries may be `StringAttribute`, `StringListAttribute`, `BooleanAttribute`,
`SelectAttribute` or `TextAreaAttribute`. **Not** another `ListAttribute`, and not
`NumberAttribute`, `HtmlAttribute`, `DynamicListAttribute` or `ToolsCallAttribute`.

```python
ListAttribute(
    name="mappings",
    title=LangString(en="Field mappings", cs="Mapování polí"),
    description=LangString(en="One row per mapped field.", cs="Jeden řádek na pole."),
    attributes=[
        StringAttribute(name="source", title=LangString(en="Source", cs="Zdroj")),
        StringAttribute(name="target", title=LangString(en="Target", cs="Cíl")),
    ],
)
```

Your attributes model receives a list of dicts keyed by the nested names.

To let each option of a nested select appear in **one row only**, set `unique_in_list=True` on it.
The builder then does not offer an option another row already picked, and disables the add button
once every option is taken. It is a builder rule, not a validation: a flow saved before you set it,
or by an older builder, can still send a repeated value, so decide in `execute()` which row wins.

```python
ListAttribute(
    name="context_values",
    title=LangString(en="Context values", cs="Kontextové hodnoty"),
    attributes=[
        SelectAttribute(
            name="key",
            title=LangString(en="Variable", cs="Proměnná"),
            options=[{"order_id": "Order ID"}, {"customer_id": "Customer ID"}],
            unique_in_list=True,
        ),
        StringAttribute(name="value", title=LangString(en="Value", cs="Hodnota")),
    ],
)
```

Worked example: `server/modules/catalog/interaction_event.py`.

### `DynamicListAttribute`

A searchable select whose options your addon supplies while the designer types — see
[chapter 9](../09-dynamic-lists.md).

| Field | Type | Notes |
|---|---|---|
| `multi_select` | `bool` | `False` (default) gives `str \| None`; `True` gives `list[str] \| None`. |

The list it queries is matched **by name**: the builder asks your addon for a `DynamicList` whose
`name` equals this attribute's `name`. Keep them identical.

```python
DynamicListAttribute(
    name="example_list",
    title=LangString(en="Department", cs="Oddělení"),
    description=LangString(en="Where to route.", cs="Kam směrovat."),
    multi_select=False,
    required=True,
)
```

### `ToolsCallAttribute`

A tool picker: the designer chooses which integrations this module may call. No extra fields.

The value reaches your module as a list of `ToolCallDefinition`, and `self.get_tool_definition()`
returns it — see [chapter 8](../08-integrations-and-tool-calls.md).

```python
ToolsCallAttribute(
    name="tools",
    title=LangString(en="Tools", cs="Nástroje"),
    description=LangString(en="Which tools this node may call.", cs="Které nástroje smí uzel volat."),
)
```

## The matching pydantic model

```python
class MyAttributes(BaseModel):
    name: str                     # NameAttribute
    greeting: str                 # StringAttribute
    prompt: str                   # TextAreaAttribute
    body: str                     # HtmlAttribute (an HTML string)
    timeout_seconds: float        # NumberAttribute
    enabled: bool                 # BooleanAttribute
    severity: str                 # SelectAttribute
    keywords: list[str]           # StringListAttribute
    mappings: list[dict]          # ListAttribute
    department: str | None        # DynamicListAttribute (list[str] | None when multi_select)
    tools: list                   # ToolsCallAttribute
```

The class is for your type-checker; `input_attributes` is what the builder renders and what the
request schema is generated from. Keep the names identical, and the two blocks next to each other.

## Output declarations

Not attributes, but declared on the same class.

**`OutputContext`** — names a context variable the module promises to set, so later nodes can offer
it in their pickers.

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | Must match what you pass to `add_context`. The builder shows it with a `$` prefix — `converted_amount` appears as `$converted_amount`. |
| `title` | `LangString` | |
| `description` | `LangString` | |
| `context_type` | `OutputContextType` | `text` (default), `number`, `boolean`, `object`, `array`. |
| `enabled_on_attribute` | `str \| None` | Only offer it when that attribute is set. |

**`OutputPortStatic`** — one arrow out of the node.

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | What you pass to `add_output_port`. |
| `title` | `LangString` | |
| `description` | `LangString` | Describe what the port *means* — the designer has only this. |
| `enabled_on_attribute` | `str \| None` | Only show the arrow when that attribute is set. |

**`OutputPortList`** — one arrow per item of a list the module produces.

| Field | Type | Notes |
|---|---|---|
| `name`, `title`, `description` | as above | |
| `list_name` | `str` | The context key holding the list. |
| `list_key` | `str` | The field in each item that labels its arrow. |

## Gotchas

| Gotcha | Consequence |
|---|---|
| Attribute `name` differs from the pydantic field | The value silently arrives empty |
| `SelectAttribute.default_value` is not one of the options | The model raises at import — your addon does not start |
| Relying on `unique_in_list` for correctness | Only the builder enforces it; your module can still receive a repeated value |
| A `DynamicListAttribute` whose name matches no `DynamicList` | An empty select, no error |
| Renaming an attribute after the module is in use | Existing flows lose that value |
| Adding a required attribute with no `default_value` | Existing flows break |
| Changing attributes without bumping the module's `version` | The builder keeps showing the old form — see [chapter 5](../05-module-in-the-builder.md) |
| Expecting a custom form control | Not supported. These eleven types are all the builder renders |
