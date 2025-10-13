# Interfaces

This section describes the public APIs, protocols, and interfaces exposed by the implementation.

{{#each INTERFACES}}
## {{name}}

**Type:** {{type}}

**Description:** {{description}}

**Signature:**

```{{language}}
{{signature}}
```

{{#if parameters}}
**Parameters:**

{{#each parameters}}
- `{{name}}` ({{type}}): {{description}}
{{/each}}
{{/if}}

{{#if returns}}
**Returns:** {{returns.type}} - {{returns.description}}
{{/if}}

{{#if code_reference}}
*Code Reference:* `{{code_reference.file}}:{{code_reference.line}}`
{{/if}}

{{#if examples}}
**Examples:**

```{{language}}
{{examples}}
```
{{/if}}

{{/each}}

## Interface Relationships

{{INTERFACE_RELATIONSHIPS}}

## Protocol Specifications

{{PROTOCOL_SPECS}}
