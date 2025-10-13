# Apache Kafka Wire Protocol

**Source:** https://kafka.apache.org/protocol
**Organization:** Apache Software Foundation
**Category:** Distributed Streaming Platform
**Application Profile:** Distributed Systems - Message Streaming

## Abstract

Apache Kafka uses a binary protocol over TCP for communication between clients and brokers. The protocol supports request-response message pairs with versioned APIs, enabling backward and forward compatibility. It is designed for high-throughput, low-latency message streaming in distributed systems.

## Protocol Characteristics

### Binary Protocol
- Uses binary protocol over TCP
- Network byte order (big-endian) for multi-byte integers
- Request-response message pairs
- Maintains connection ordering
- Supports versioned API compatibility

### Connection Model
- Persistent connections recommended
- No mandatory handshake required
- Single TCP connection processes requests sequentially
- Supports non-blocking IO
- Request pipelining supported

## Protocol Primitive Types

### Numeric Types
- **BOOLEAN**: Single byte (0 or 1)
- **INT8**: 8-bit signed integer
- **INT16**: 16-bit signed integer
- **INT32**: 32-bit signed integer
- **INT64**: 64-bit signed integer
- **UINT16**: 16-bit unsigned integer
- **UINT32**: 32-bit unsigned integer
- **VARINT**: Variable-length signed integer
- **VARLONG**: Variable-length signed long
- **FLOAT64**: IEEE 754 double precision

### String and Array Types
- **STRING**: Length-prefixed UTF-8 string
- **COMPACT_STRING**: Varint-length-prefixed string
- **NULLABLE_STRING**: String or null (-1 length)
- **BYTES**: Length-prefixed byte array
- **COMPACT_BYTES**: Varint-length-prefixed bytes
- **ARRAY**: Length-prefixed array of elements
- **COMPACT_ARRAY**: Varint-length-prefixed array

### Other Types
- **UUID**: 16-byte universally unique identifier
- **RECORDS**: Batch of records (see Record Batch format)
- **TAGGED_FIELDS**: Flexible version field extensions

## Request/Response Format

### Request Structure
```
RequestMessage → Size RequestHeader RequestPayload
  Size → INT32 (message size excluding this field)
  RequestHeader → ApiKey ApiVersion CorrelationId ClientId
    ApiKey → INT16
    ApiVersion → INT16
    CorrelationId → INT32
    ClientId → NULLABLE_STRING
  RequestPayload → (API-specific structure)
```

### Response Structure
```
ResponseMessage → Size ResponseHeader ResponsePayload
  Size → INT32
  ResponseHeader → CorrelationId
    CorrelationId → INT32
  ResponsePayload → (API-specific structure)
```

### Correlation ID
- Client-provided identifier
- Links request to response
- Echo'd back by server
- Enables request pipelining

## Message Format

### Record Batch Format
```
RecordBatch →
  BaseOffset: INT64
  BatchLength: INT32
  PartitionLeaderEpoch: INT32
  Magic: INT8 (current value is 2)
  CRC: UINT32
  Attributes: INT16
  LastOffsetDelta: INT32
  BaseTimestamp: INT64
  MaxTimestamp: INT64
  ProducerId: INT64
  ProducerEpoch: INT16
  BaseSequence: INT32
  RecordsCount: INT32
  Records: [Record]
```

### Record Format
```
Record →
  Length: VARINT
  Attributes: INT8
  TimestampDelta: VARLONG
  OffsetDelta: VARINT
  KeyLength: VARINT
  Key: BYTES
  ValueLength: VARINT
  Value: BYTES
  HeadersCount: VARINT
  Headers: [Header]
```

### Record Attributes
- **Compression**: None, GZIP, Snappy, LZ4, ZSTD
- **Timestamp Type**: Create time or log append time
- **Transactional**: Part of transaction
- **Control**: Control message (not user data)

## Key Protocol APIs

### Metadata API
- **Purpose**: Discover cluster topology
- **Request**: List of topics or null for all
- **Response**: Broker list, topic partitions, leaders, replicas
- **Use**: Client bootstrap, leader discovery

### Produce API
- **Purpose**: Send messages to topics
- **Request**: Topic, partition, record batch, acks
- **Response**: Partition, base offset, timestamp, error
- **Features**: Batching, compression, idempotence, transactions

#### Producer Acknowledgments
- **acks=0**: No acknowledgment
- **acks=1**: Leader acknowledgment only
- **acks=all**: All in-sync replicas acknowledge

### Fetch API
- **Purpose**: Retrieve messages from topics
- **Request**: Topic, partition, offset, max bytes
- **Response**: Records, high watermark, error
- **Features**: Incremental fetch sessions, isolation level

#### Fetch Session
- Incremental fetch requests
- Reduces bandwidth for metadata
- Session ID and epoch tracking
- Forgotten topics handling

### ListOffsets API
- **Purpose**: Query partition offsets
- **Request**: Topic, partition, timestamp
- **Response**: Offset, timestamp
- **Use**: Consumer positioning, time-based seeking

### OffsetCommit API
- **Purpose**: Commit consumer group offsets
- **Request**: Group, topic, partition, offset, metadata
- **Response**: Error status per partition
- **Use**: Consumer progress tracking

### OffsetFetch API
- **Purpose**: Retrieve committed offsets
- **Request**: Group, topic, partition
- **Response**: Offset, metadata, error
- **Use**: Consumer startup positioning

### JoinGroup API
- **Purpose**: Join consumer group
- **Request**: Group ID, member ID, protocols
- **Response**: Generation ID, leader, members
- **Use**: Consumer group coordination

### SyncGroup API
- **Purpose**: Synchronize group assignments
- **Request**: Group ID, generation, assignments
- **Response**: Member assignment
- **Use**: Partition assignment distribution

### Heartbeat API
- **Purpose**: Maintain group membership
- **Request**: Group ID, generation, member ID
- **Response**: Error status
- **Use**: Keep consumer alive, trigger rebalance

### LeaveGroup API
- **Purpose**: Leave consumer group
- **Request**: Group ID, member ID
- **Response**: Error status
- **Use**: Clean group exit

### CreateTopics API
- **Purpose**: Create topics
- **Request**: Topic configs, partitions, replication factor
- **Response**: Error status per topic
- **Use**: Administrative topic creation

### DeleteTopics API
- **Purpose**: Delete topics
- **Request**: Topic names
- **Response**: Error status per topic
- **Use**: Administrative topic deletion

## Error Codes

### Common Error Codes
- **0**: No error
- **-1**: Unknown server error
- **1**: Offset out of range
- **2**: Corrupt message
- **3**: Unknown topic or partition
- **6**: Not leader for partition
- **10**: Message too large
- **14**: Offset metadata too large
- **15**: Network exception
- **16**: Group coordinator not available
- **25**: Not controller
- **27**: Not enough replicas
- **28**: Not enough replicas after append
- **65**: Request timeout
- **101**: Transaction coordinator not found

## Versioning and Compatibility

### API Versioning
- Each API has version number
- Request specifies version
- Server supports version range
- Newer clients work with older servers
- Newer servers work with older clients

### Schema Evolution
- Tagged fields for flexible versions
- Optional fields added without breaking changes
- Deprecated fields maintained for compatibility
- Protocol documentation generation

## Transactions

### Transactional Writes
- **InitProducerId**: Initialize producer transaction
- **BeginTransaction**: Start transaction
- **AddPartitionsToTxn**: Add partitions
- **EndTransaction**: Commit or abort
- **AddOffsetsToTxn**: Include consumer offsets

### Transactional Reads
- **Isolation Level**: Read uncommitted or read committed
- Control records mark transaction boundaries
- Aborted messages filtered by consumer

## Security

### Authentication
- **SASL/PLAIN**: Username/password
- **SASL/SCRAM**: Challenge-response
- **SASL/GSSAPI**: Kerberos
- **SASL/OAUTHBEARER**: OAuth tokens

### Authorization
- ACLs for topics, groups, clusters
- User/principal-based permissions
- Operations: read, write, create, delete, etc.

### Encryption
- **SSL/TLS**: Transport encryption
- Certificate-based authentication
- Mutual TLS support

## Performance Optimization

### Batching
- Producer batches messages
- Reduces network overhead
- Configurable batch size and linger time
- Compression at batch level

### Zero-Copy Transfer
- Sendfile system call
- Direct transfer from disk to network
- Reduces CPU and memory overhead
- Optimized for consumer reads

### Partition Assignment
- Range, round-robin, sticky strategies
- Cooperative rebalancing
- Minimizes partition movement
- Maintains consumer affinity

## Use Cases in Distributed Systems

1. **Event Sourcing**: Durable event log with ordering guarantees
2. **Stream Processing**: Real-time data pipelines and transformations
3. **Log Aggregation**: Centralized logging from multiple services
4. **Messaging**: Pub-sub messaging between microservices
5. **Metrics Collection**: Time-series data ingestion and distribution
6. **Change Data Capture**: Database change stream processing

## Implementation Considerations

### Producer Best Practices
- Configure appropriate acks level
- Enable idempotence for exactly-once semantics
- Use compression for large messages
- Implement proper error handling and retries
- Monitor producer metrics

### Consumer Best Practices
- Use consumer groups for scalability
- Commit offsets appropriately
- Handle rebalances gracefully
- Monitor consumer lag
- Implement proper shutdown

### Broker Configuration
- Replication factor for durability
- Partition count for parallelism
- Retention policies for storage management
- Log compaction for changelog topics
- Security and authentication settings

### Monitoring and Operations
- Topic and partition metrics
- Producer and consumer metrics
- Broker health and performance
- Under-replicated partitions
- Consumer group lag
