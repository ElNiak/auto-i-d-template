# RFC 6570: URI Templates

**Source:** IETF RFC 6570
**URL:** https://www.rfc-editor.org/rfc/rfc6570.txt
**Published:** March 2012
**Category:** Standards Track

## Abstract

A URI Template is a compact way to describe a range of Uniform Resource Identifiers through variable expansion. It provides a mechanism for abstracting resource identifier spaces by allowing variable parts to be easily identified and described.

## Introduction

URI Templates allow:
- **Abstraction**: Define URI patterns with placeholders
- **Generation**: Create concrete URIs by expanding variables
- **Discovery**: Help clients understand URI structure
- **Flexibility**: Support various expansion behaviors

## Levels of Complexity

URI Templates are defined across four levels:

### Level 1: Simple String Expansion

Basic variable substitution without encoding restrictions.

**Syntax:** `{var}`

**Example:**
```
Template: http://example.com/~{username}/
Variables: username = "fred"
Result:   http://example.com/~fred/
```

### Level 2: Reserved Expansion and Fragments

Adds support for reserved characters and fragment identifiers.

**Operators:** `+` (reserved), `#` (fragment)

**Examples:**
```
Template: http://example.com/dictionary/{term:1}/{term}
Template: http://example.com/search{?q,lang}
Template: http://example.com/page.html#{section}
```

### Level 3: Multiple Variables and Separators

Supports multiple variables with various separator types.

**Operators:** `.` (label), `/` (path), `;` (parameter), `?` (query), `&` (continuation)

**Examples:**
```
Template: http://example.com{/path*}
Variables: path = ["foo", "bar"]
Result:   http://example.com/foo/bar

Template: http://example.com/search{?q,lang}
Variables: q = "cat", lang = "en"
Result:   http://example.com/search?q=cat&lang=en
```

### Level 4: Value Modifiers

Adds prefix and explode modifiers for advanced expansion.

**Modifiers:**
- `:n` - Prefix (first n characters)
- `*` - Explode (expand composite values)

**Examples:**
```
Template: http://example.com/search{?q,lang,region*}
Variables: q = "cat", lang = "en", region = {"country": "US", "state": "CA"}
Result:   http://example.com/search?q=cat&lang=en&country=US&state=CA
```

## Expression Types

### Simple String Expansion: {var}

- Encodes unreserved characters
- Encodes reserved characters as %XX
- Used for simple variable substitution

**Example:**
```
Template: {var}
Variables: var = "value"
Result:   value
```

### Reserved Expansion: {+var}

- Allows reserved characters to pass through unencoded
- Useful for URIs within URIs

**Example:**
```
Template: {+path}/here
Variables: path = "/foo/bar"
Result:   /foo/bar/here
```

### Fragment Expansion: {#var}

- Expands variables into fragment identifiers
- Prefixed with `#`

**Example:**
```
Template: foo{#section}
Variables: section = "intro"
Result:   foo#intro
```

### Label Expansion: {.var}

- Expands variables as dot-prefixed labels
- Used for domain label expansion

**Example:**
```
Template: X{.var}
Variables: var = "value"
Result:   X.value
```

### Path Segment Expansion: {/var}

- Expands variables as slash-prefixed path segments
- Used for hierarchical paths

**Example:**
```
Template: http://example.com{/var}
Variables: var = "value"
Result:   http://example.com/value
```

### Path-Style Parameter Expansion: {;var}

- Expands variables as semicolon-prefixed parameters
- Used for matrix URI parameters

**Example:**
```
Template: {;x,y}
Variables: x = "1024", y = "768"
Result:   ;x=1024;y=768
```

### Form-Style Query Expansion: {?var}

- Expands variables as query parameters
- Prefixed with `?`

**Example:**
```
Template: http://example.com/search{?q,lang}
Variables: q = "cat", lang = "en"
Result:   http://example.com/search?q=cat&lang=en
```

### Form-Style Query Continuation: {&var}

- Expands variables as additional query parameters
- Prefixed with `&`

**Example:**
```
Template: http://example.com/search?fixed=yes{&x}
Variables: x = "new"
Result:   http://example.com/search?fixed=yes&x=new
```

## Variable Types

### Simple Values

Single string values:
```
Template: {var}
Variables: var = "hello"
Result:   hello
```

### List Values

Arrays of strings:
```
Template: {var*}
Variables: var = ["red", "green", "blue"]
Result:   red,green,blue

Template: {/var*}
Variables: var = ["red", "green", "blue"]
Result:   /red/green/blue
```

### Associative Array Values

Key-value pairs:
```
Template: {?var*}
Variables: var = {"semi": ";", "dot": ".", "comma": ","}
Result:   ?semi=%3B&dot=.&comma=%2C
```

## Modifiers

### Prefix Modifier: :n

Limits expansion to first n characters:
```
Template: {var:3}
Variables: var = "value"
Result:   val
```

### Explode Modifier: *

Expands composite values:
```
Template: {/list*}
Variables: list = ["one", "two", "three"]
Result:   /one/two/three

Template: {?keys*}
Variables: keys = {"a": "1", "b": "2"}
Result:   ?a=1&b=2
```

## Encoding Rules

### Unreserved Characters

Not encoded:
```
A-Z a-z 0-9 - . _ ~
```

### Reserved Characters

Encoded in simple expansion:
```
: / ? # [ ] @ ! $ & ' ( ) * + , ; =
```

### Percent Encoding

Format: `%XX` where XX is hexadecimal ASCII value

**Examples:**
- Space: `%20`
- `!`: `%21`
- `#`: `%23`
- `$`: `%24`

## API Design Patterns

### Resource Collections

```
Template: http://api.example.com/{collection}
Variables: collection = "users"
Result:   http://api.example.com/users
```

### Resource Identifiers

```
Template: http://api.example.com/{collection}/{id}
Variables: collection = "users", id = "123"
Result:   http://api.example.com/users/123
```

### Nested Resources

```
Template: http://api.example.com/{collection}/{id}/{subcollection}
Variables: collection = "users", id = "123", subcollection = "posts"
Result:   http://api.example.com/users/123/posts
```

### Query Parameters

```
Template: http://api.example.com/search{?q,limit,offset}
Variables: q = "REST", limit = "10", offset = "0"
Result:   http://api.example.com/search?q=REST&limit=10&offset=0
```

### Filtering

```
Template: http://api.example.com/{collection}{?filter*}
Variables: collection = "users", filter = {"status": "active", "role": "admin"}
Result:   http://api.example.com/users?status=active&role=admin
```

### Pagination

```
Template: http://api.example.com/{collection}{?page,per_page}
Variables: collection = "users", page = "2", per_page = "50"
Result:   http://api.example.com/users?page=2&per_page=50
```

### Versioning

```
Template: http://api.example.com/{version}/{collection}
Variables: version = "v1", collection = "users"
Result:   http://api.example.com/v1/users
```

## Best Practices

### API Documentation

1. **Document templates**: Show URI templates in API documentation
2. **Explain variables**: Describe each variable's purpose and constraints
3. **Provide examples**: Include expansion examples for clarity

### Client Implementation

1. **Use template libraries**: Don't implement expansion manually
2. **Validate inputs**: Check variable values before expansion
3. **Handle errors**: Gracefully handle invalid templates or variables

### Server Implementation

1. **Parse consistently**: Use template-aware routing
2. **Extract variables**: Parse incoming URIs to extract variable values
3. **Validate extractions**: Ensure extracted values meet expectations

### Design Considerations

1. **Predictable structure**: Use consistent template patterns
2. **Avoid ambiguity**: Ensure templates expand unambiguously
3. **Consider encoding**: Be aware of which characters need encoding
4. **Document constraints**: Specify variable value restrictions

## Common Pitfalls

1. **Over-encoding**: Don't double-encode already-encoded values
2. **Missing modifiers**: Use `*` for lists and objects in queries
3. **Wrong operators**: Choose appropriate operators for context
4. **Undefined variables**: Handle missing variables gracefully

## Security Considerations

1. **Injection attacks**: Validate variable values to prevent injection
2. **Information disclosure**: Be careful with template disclosure
3. **Resource enumeration**: Consider if templates reveal system structure
4. **Access control**: Validate authorization for expanded URIs

## References

- Full RFC text: https://www.rfc-editor.org/rfc/rfc6570.txt
- Related standards:
  - RFC 3986 (URI Generic Syntax)
  - RFC 3987 (IRIs)

---

**Key Takeaways for REST API Design:**

1. Use URI Templates to document and communicate API URI structure
2. Choose appropriate operators for different URI components (query, path, fragment)
3. Use the explode modifier (*) for lists and objects
4. Document variable constraints and types
5. Implement proper percent-encoding based on expansion type
6. Use templates for consistent URI construction in clients
7. Consider template-aware routing in servers
8. Validate variables before expansion to prevent security issues
