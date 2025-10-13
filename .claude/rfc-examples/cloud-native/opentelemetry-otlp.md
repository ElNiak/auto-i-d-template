# OpenTelemetry Protocol (OTLP) Specification

**Source**: https://opentelemetry.io/docs/specs/otlp/
**Source**: https://github.com/open-telemetry/opentelemetry-proto
**Type**: CNCF OpenTelemetry project specification
**Domain**: Observability telemetry data transport
**Version**: 1.8.0 (current stable)

## Overview

The OpenTelemetry Protocol (OTLP) defines the encoding, transport, and delivery mechanism of telemetry data between telemetry sources, intermediate nodes (collectors), and telemetry backends.

### Core Design Principles

1. **General-Purpose Protocol**: Works for traces, metrics, logs, and profiles
2. **Request-Response Style**: Client sends request, server responds
3. **Multiple Transport Options**: gRPC and HTTP transports
4. **Flexible Encoding**: Binary Protobuf and JSON Protobuf
5. **Versioning Strategy**: Capability-based, not version numbers
6. **Backward Compatibility**: Strong guarantees for stable signals

### Signal Stability Status

- **Traces**: Stable
- **Metrics**: Stable
- **Logs**: Stable
- **Profiles**: Development (experimental)

## Transport Mechanisms

### OTLP/gRPC

**Default Port**: 4317

**Protocol**: HTTP/2-based gRPC

**Service Definitions**:
```protobuf
service TraceService {
  rpc Export(ExportTraceServiceRequest) returns (ExportTraceServiceResponse) {}
}

service MetricsService {
  rpc Export(ExportMetricsServiceRequest) returns (ExportMetricsServiceResponse) {}
}

service LogsService {
  rpc Export(ExportLogsServiceRequest) returns (ExportLogsServiceResponse) {}
}
```

**Characteristics**:
- Unary requests (not streaming by default)
- Supports concurrent requests
- Built-in flow control (HTTP/2)
- Efficient binary encoding
- Automatic reconnection handling

**Endpoint Format**:
```
http[s]://<host>:<port>/opentelemetry.proto.<signal>.v1.<Signal>Service/Export
```

**Examples**:
- `https://collector.example.com:4317/opentelemetry.proto.trace.v1.TraceService/Export`
- `https://collector.example.com:4317/opentelemetry.proto.metrics.v1.MetricsService/Export`

### OTLP/HTTP

**Default Port**: 4318

**Protocol**: HTTP/1.1 or HTTP/2

**Method**: POST

**Default Paths**:
- Traces: `/v1/traces`
- Metrics: `/v1/metrics`
- Logs: `/v1/logs`
- Profiles: `/v1development/profiles` (experimental)

**Full URL Examples**:
```
https://collector.example.com:4318/v1/traces
https://collector.example.com:4318/v1/metrics
https://collector.example.com:4318/v1/logs
```

**Characteristics**:
- Works with standard HTTP infrastructure
- Supports proxies, load balancers, CDNs
- Two encoding options (binary/JSON)
- Simpler firewall traversal

## Data Encoding

### Binary Protobuf Encoding

**Content-Type**: `application/x-protobuf`

**Encoding**: proto3 standard binary encoding

**Characteristics**:
- Compact representation
- Fast serialization/deserialization
- Language-agnostic
- Schema-driven

**Usage**:
- Default for OTLP/gRPC
- Recommended for OTLP/HTTP (better performance)

### JSON Protobuf Encoding

**Content-Type**: `application/json`

**Encoding**: proto3 JSON mapping with OTLP-specific deviations

**Characteristics**:
- Human-readable
- Debuggable
- Easier integration with web technologies
- Larger payload size

**OTLP-Specific JSON Rules**:

1. **64-bit Integers**: Encoded as decimal strings (not numbers)
   ```json
   {
     "timeUnixNano": "1609459200000000000"
   }
   ```

2. **Byte Arrays**: Hex-encoded strings
   ```json
   {
     "traceId": "5b8efff798038103d269b633813fc60c"
   }
   ```

3. **Enum Values**: Uppercase strings (not integers)
   ```json
   {
     "aggregationTemporality": "AGGREGATION_TEMPORALITY_CUMULATIVE"
   }
   ```

4. **Field Names**: camelCase (not snake_case)
   ```json
   {
     "spanId": "abc123",
     "startTimeUnixNano": "1609459200000000000"
   }
   ```

## Request Structure

### Common Pattern

All OTLP export requests follow similar structure:

```protobuf
message Export<Signal>ServiceRequest {
  repeated ResourceSpans resource_spans = 1;  // for traces
  // or
  repeated ResourceMetrics resource_metrics = 1;  // for metrics
  // or
  repeated ResourceLogs resource_logs = 1;  // for logs
}
```

### Hierarchical Data Model

**Three-Level Hierarchy**:

1. **Resource**: Describes entity producing telemetry
2. **Instrumentation Scope**: Library/module within resource
3. **Telemetry Data**: Individual spans/metrics/logs

```
Resource
  ├── Instrumentation Scope 1
  │     ├── Span 1
  │     ├── Span 2
  │     └── Span 3
  └── Instrumentation Scope 2
        ├── Span 4
        └── Span 5
```

### Example: Trace Request Structure

```json
{
  "resourceSpans": [
    {
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "my-service"}},
          {"key": "service.version", "value": {"stringValue": "1.0.0"}},
          {"key": "host.name", "value": {"stringValue": "server-01"}}
        ]
      },
      "scopeSpans": [
        {
          "scope": {
            "name": "my-instrumentation-library",
            "version": "0.1.0"
          },
          "spans": [
            {
              "traceId": "5b8efff798038103d269b633813fc60c",
              "spanId": "eee19b7ec3c1b174",
              "name": "GET /api/users",
              "kind": "SPAN_KIND_SERVER",
              "startTimeUnixNano": "1609459200000000000",
              "endTimeUnixNano": "1609459200050000000",
              "attributes": [
                {"key": "http.method", "value": {"stringValue": "GET"}},
                {"key": "http.status_code", "value": {"intValue": "200"}}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## Response Structure

### Success Response

**Full Success**:
```protobuf
message Export<Signal>ServiceResponse {
  <Signal>PartialSuccess partial_success = 1;
}

message <Signal>PartialSuccess {
  int64 rejected_<items> = 1;
  string error_message = 2;
}
```

**Full Success Example** (all data accepted):
```json
{
  "partialSuccess": {
    "rejectedSpans": "0"
  }
}
```

**HTTP Status**: `200 OK`

### Partial Success Response

Some data accepted, some rejected:

```json
{
  "partialSuccess": {
    "rejectedSpans": "5",
    "errorMessage": "Spans with invalid trace IDs were rejected"
  }
}
```

**HTTP Status**: `200 OK`

**Interpretation**:
- Response still indicates success
- Client checks `rejectedSpans` > 0 for partial failure
- `errorMessage` provides human-readable details

### Failure Response

**OTLP/gRPC**: Uses standard gRPC status codes

**OTLP/HTTP**: Uses HTTP status codes

## Error Handling

### Error Categories

**1. Retryable Errors**:
- Temporary server unavailability
- Resource exhaustion (rate limiting)
- Network timeouts

**Client Action**: Retry with backoff

**2. Non-Retryable Errors**:
- Invalid request format
- Authentication/authorization failure
- Unsupported data

**Client Action**: Do not retry, log error, drop data or alert

### HTTP Status Codes

| Status Code | Category | Retry? | Description |
|-------------|----------|--------|-------------|
| 200 OK | Success | N/A | Request successful (check partial success) |
| 400 Bad Request | Non-Retryable | No | Invalid request format |
| 401 Unauthorized | Non-Retryable | No | Authentication required |
| 403 Forbidden | Non-Retryable | No | Authorization failed |
| 404 Not Found | Non-Retryable | No | Endpoint not found |
| 405 Method Not Allowed | Non-Retryable | No | Wrong HTTP method |
| 413 Payload Too Large | Retryable* | Yes | Request too large (split and retry) |
| 429 Too Many Requests | Retryable | Yes | Rate limited (backoff) |
| 500 Internal Server Error | Retryable | Yes | Temporary server error |
| 502 Bad Gateway | Retryable | Yes | Upstream server error |
| 503 Service Unavailable | Retryable | Yes | Server overloaded |
| 504 Gateway Timeout | Retryable | Yes | Upstream timeout |

\* 413 is retryable only if client splits the request into smaller batches

### gRPC Status Codes

| gRPC Code | Category | Retry? | Description |
|-----------|----------|--------|-------------|
| OK | Success | N/A | Request successful |
| CANCELLED | Retryable | Yes | Request cancelled |
| INVALID_ARGUMENT | Non-Retryable | No | Invalid data |
| DEADLINE_EXCEEDED | Retryable | Yes | Request timeout |
| NOT_FOUND | Non-Retryable | No | Endpoint not found |
| PERMISSION_DENIED | Non-Retryable | No | Authorization failed |
| RESOURCE_EXHAUSTED | Retryable | Yes | Rate limited |
| FAILED_PRECONDITION | Non-Retryable | No | Invalid state |
| UNIMPLEMENTED | Non-Retryable | No | Method not supported |
| UNAVAILABLE | Retryable | Yes | Server unavailable |

### Retry Strategy

**Exponential Backoff**:

```
retry_delay = min(initial_delay * (backoff_multiplier ^ retry_count), max_delay)
```

**Recommended Parameters**:
- `initial_delay`: 1 second
- `backoff_multiplier`: 2
- `max_delay`: 30 seconds
- `max_retries`: 5

**Example Sequence**:
1. Attempt 1: Immediate
2. Attempt 2: Wait 1s
3. Attempt 3: Wait 2s
4. Attempt 4: Wait 4s
5. Attempt 5: Wait 8s
6. Attempt 6: Wait 16s
7. Give up after 5 retries

**Jitter**: Add random variation to prevent thundering herd

```
actual_delay = retry_delay * (0.5 + random(0, 0.5))
```

### Throttling

**Retry-After Header** (HTTP):

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 120

Server is temporarily unavailable. Retry after 120 seconds.
```

**Client Behavior**:
- Honor `Retry-After` header value
- Do not retry before specified time
- If missing, use exponential backoff

## Compression

### Supported Compression Algorithms

Servers MUST support:
- **none**: No compression
- **gzip**: Standard gzip compression

Servers MAY support:
- **zstd**: Zstandard compression (better performance)
- **snappy**: Snappy compression (fast)

### OTLP/gRPC Compression

**Request**:
```
grpc-encoding: gzip
```

**Response**:
```
grpc-encoding: gzip
```

Negotiated via gRPC metadata.

### OTLP/HTTP Compression

**Request Compression**:
```http
POST /v1/traces HTTP/1.1
Content-Encoding: gzip
Content-Type: application/x-protobuf

<compressed binary data>
```

**Response Compression**:
```http
HTTP/1.1 200 OK
Content-Encoding: gzip
Content-Type: application/x-protobuf

<compressed binary data>
```

Client indicates supported compression in `Accept-Encoding` header:

```http
Accept-Encoding: gzip, deflate
```

## Concurrency and Batching

### Concurrent Requests

Clients MAY send multiple concurrent requests:

- **High-throughput scenarios**: Increases parallelism
- **Per-destination queues**: Separate queue per backend
- **Configurable concurrency**: Default 1, can increase

**Benefits**:
- Better throughput
- Reduced latency
- Efficient use of HTTP/2 multiplexing (gRPC)

**Considerations**:
- Server must handle concurrent requests
- Ordering not guaranteed across requests
- Each request processed independently

### Batching

Clients SHOULD batch telemetry data:

**Benefits**:
- Reduced network overhead
- Better compression ratios
- Fewer TLS handshakes
- Lower per-request costs

**Parameters**:
- **Batch size**: Number of items per request
- **Batch timeout**: Maximum wait time before sending

**Example Configuration**:
```yaml
batch_processor:
  timeout: 1s
  send_batch_size: 1024
  send_batch_max_size: 2048
```

## Authentication and Security

### HTTP Authentication

**Bearer Token**:
```http
POST /v1/traces HTTP/1.1
Authorization: Bearer <token>
```

**API Key**:
```http
POST /v1/traces HTTP/1.1
X-API-Key: <key>
```

**Basic Auth**:
```http
POST /v1/traces HTTP/1.1
Authorization: Basic <base64(username:password)>
```

### gRPC Authentication

**Metadata**:
```
authorization: Bearer <token>
```

**TLS Client Certificates**: Mutual TLS (mTLS)

### TLS/SSL

**Recommended**: Use TLS for all production deployments

**OTLP/gRPC**:
- Default: Insecure connection
- TLS: Port 4317 with TLS enabled
- mTLS: Client certificate verification

**OTLP/HTTP**:
- Default: HTTP (insecure)
- HTTPS: TLS-enabled connection
- mTLS: Client certificate verification

## Multi-Destination Exporting

### Pattern

Exporters may send data to multiple backends:

```
Telemetry Source
  ├── Exporter → Backend A
  ├── Exporter → Backend B
  └── Exporter → Backend C
```

### Implementation Recommendations

**1. Per-Destination Queuing**:
- Separate queue for each destination
- Independent retry logic
- Isolated failure domains

**2. Shared Data References**:
- Use immutable data structures
- Share references (don't deep copy)
- Reduces memory overhead

**3. Independent Acknowledgment**:
- Success at Backend A doesn't affect Backend B
- Failures isolated per destination
- Different retry strategies per backend

## Empty Telemetry Envelopes

### Definition

Request with resource/scope but no actual telemetry data:

```json
{
  "resourceSpans": [
    {
      "resource": {
        "attributes": [...]
      },
      "scopeSpans": [
        {
          "scope": {...},
          "spans": []  // Empty!
        }
      ]
    }
  ]
}
```

### Recommendations

**Senders**:
- SHOULD NOT create empty envelopes
- Optimize to avoid sending requests with no data

**Receivers**:
- MAY ignore empty envelopes
- MAY drop empty envelopes without error
- SHOULD NOT fail on empty envelopes

## Versioning and Compatibility

### Versioning Strategy

OTLP does NOT use explicit version numbers.

**Instead**: Capability-based compatibility

### Protobuf Schema Evolution

**Backward-Compatible Changes** (allowed):
- Add new optional fields
- Add new enum values
- Add new message types
- Add new methods/services

**Breaking Changes** (prohibited for stable signals):
- Remove fields
- Change field types
- Change field numbers
- Rename fields
- Change field from optional to required

### Capability Discovery

Clients and servers discover capabilities through:

1. **Protobuf Reflection**: Query supported services/methods
2. **Partial Success Responses**: Indicate what was rejected
3. **Error Messages**: Describe unsupported features

### Interoperability Principles

**Forward Compatibility**:
- Receivers MUST ignore unknown fields
- Receivers MUST handle unknown enum values gracefully

**Backward Compatibility**:
- Senders MAY omit optional fields
- Receivers MUST handle missing optional fields

**Example**: Client sends new field introduced in OTLP 1.5 to server implementing OTLP 1.3:
- Server ignores unknown field (forward compatible)
- Server processes known fields normally
- No error, data processed successfully

## Telemetry Data Models

### Resource Attributes

Common resource attributes:

| Attribute | Type | Example |
|-----------|------|---------|
| service.name | string | "my-service" |
| service.version | string | "1.0.0" |
| service.instance.id | string | "pod-abc123" |
| host.name | string | "server-01" |
| host.type | string | "n2-standard-4" |
| cloud.provider | string | "gcp" |
| cloud.region | string | "us-central1" |
| k8s.namespace.name | string | "production" |
| k8s.pod.name | string | "app-7d8f9c-abc" |

### Instrumentation Scope

Identifies library/module producing telemetry:

```json
{
  "name": "io.opentelemetry.contrib.mongodb",
  "version": "1.2.3",
  "attributes": [
    {"key": "library.language", "value": {"stringValue": "java"}}
  ]
}
```

### Span Attributes (Traces)

Common span attributes:

| Attribute | Type | Example |
|-----------|------|---------|
| http.method | string | "GET" |
| http.url | string | "https://api.example.com/users" |
| http.status_code | int | 200 |
| db.system | string | "postgresql" |
| db.statement | string | "SELECT * FROM users" |
| rpc.service | string | "UserService" |
| rpc.method | string | "GetUser" |

### Metric Types

**Supported Metric Types**:
- **Gauge**: Point-in-time value
- **Sum**: Cumulative or delta value
- **Histogram**: Distribution of values
- **Exponential Histogram**: Distribution with exponential buckets
- **Summary**: Quantiles (legacy, use histogram)

### Log Attributes

Common log attributes:

| Attribute | Type | Example |
|-----------|------|---------|
| log.level | string | "ERROR" |
| log.message | string | "Connection failed" |
| exception.type | string | "java.net.SocketException" |
| exception.message | string | "Connection reset" |
| exception.stacktrace | string | "at com.example..." |

## Configuration via Environment Variables

### Endpoint Configuration

**OTLP/gRPC**:
```bash
OTEL_EXPORTER_OTLP_ENDPOINT="https://collector.example.com:4317"
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="https://traces.example.com:4317"
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT="https://metrics.example.com:4317"
```

**OTLP/HTTP**:
```bash
OTEL_EXPORTER_OTLP_ENDPOINT="https://collector.example.com:4318"
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="https://collector.example.com:4318/v1/traces"
```

### Authentication

```bash
OTEL_EXPORTER_OTLP_HEADERS="authorization=Bearer <token>,x-custom-header=value"
```

### Protocol Selection

```bash
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"  # or "http/protobuf" or "http/json"
```

### Timeout Configuration

```bash
OTEL_EXPORTER_OTLP_TIMEOUT="10000"  # milliseconds
```

### Compression

```bash
OTEL_EXPORTER_OTLP_COMPRESSION="gzip"  # or "none"
```

## Performance Considerations

### Batching Strategy

**Optimal batch size**: Balance latency vs throughput
- Small batches: Lower latency, higher overhead
- Large batches: Higher latency, better compression

**Typical values**:
- Batch timeout: 1-5 seconds
- Batch size: 512-2048 items

### Binary Protobuf vs JSON

**Binary Protobuf**:
- 3-10x smaller payload
- Faster serialization
- Better for high-volume production

**JSON**:
- Human-readable (debugging)
- Easier integration (web/browser)
- Acceptable for low-volume scenarios

### Compression Impact

**gzip compression**:
- Reduces payload by 60-90% (typical)
- Adds CPU overhead (minor)
- Recommended for all production deployments

**zstd compression** (if supported):
- Better compression ratio than gzip
- Faster compression/decompression
- Ideal for very high throughput

### Connection Reuse

- OTLP/gRPC: Automatically reuses HTTP/2 connections
- OTLP/HTTP: Use HTTP keep-alive for connection reuse

**Benefits**:
- Avoids TLS handshake overhead
- Reduces connection establishment latency
- Better throughput

## Cloud-Native Design Patterns

### 1. Capability-Based Versioning
- No explicit version numbers
- Protobuf schema evolution
- Forward and backward compatibility

### 2. Request-Response Pattern
- Stateless protocol
- Each request independent
- Horizontal scalability

### 3. Partial Success Handling
- Graceful degradation
- Some data better than no data
- Detailed error reporting

### 4. Multi-Transport Support
- gRPC for efficiency
- HTTP for ubiquity
- Same data model

### 5. Hierarchical Data Model
- Resource → Scope → Data
- Efficient grouping
- Clear attribution

### 6. Extensible Schema
- Optional fields
- Unknown field handling
- Future-proof design

### 7. Observability for Observability
- Protocol designed for telemetry
- Handles high-volume data
- Low-latency requirements

### 8. Vendor-Neutral Standard
- CNCF project
- Open specification
- Multiple implementations

## Summary of Key Patterns

1. **Request-response protocol** with strong retry semantics
2. **Multi-transport support** (gRPC and HTTP)
3. **Flexible encoding** (binary Protobuf and JSON)
4. **Capability-based versioning** without explicit version numbers
5. **Hierarchical data model** (Resource → Scope → Data)
6. **Partial success handling** for graceful degradation
7. **Compression support** for efficient transmission
8. **Concurrent requests** for high throughput
9. **Batch processing** to optimize network usage
10. **Strong backward compatibility** guarantees for stable signals

These patterns make OTLP a robust, efficient, and future-proof protocol for transmitting observability telemetry data in cloud-native environments.
