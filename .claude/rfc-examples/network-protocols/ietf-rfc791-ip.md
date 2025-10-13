# RFC 791 - Internet Protocol (IP)

**Source:** IETF RFC 791
**URL:** https://www.rfc-editor.org/rfc/rfc791.txt
**Category:** Network Protocol - Network Layer

## Protocol Overview

The Internet Protocol (IP) is designed for use in interconnected packet-switched computer communication networks. It provides the fundamental mechanism for transmitting blocks of data (datagrams) from sources to destinations across network boundaries. IP is connectionless, treating each datagram independently without regard to prior or subsequent transmissions.

## Key Characteristics

- **Connectionless:** No connection establishment required before data transmission
- **Best-Effort Delivery:** No guarantees of delivery, ordering, or duplicate prevention
- **Datagram-Oriented:** Each packet independent and self-contained
- **Addressing:** 32-bit addresses identify source and destination hosts
- **Fragmentation:** Supports breaking datagrams into smaller fragments
- **Routing:** Enables forwarding across multiple networks
- **Minimal State:** Routers need not maintain per-flow information

## IP Datagram Header Format

```
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |Version|  IHL  |Type of Service|          Total Length         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |         Identification        |Flags|      Fragment Offset    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Time to Live |    Protocol   |         Header Checksum       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                       Source Address                          |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Destination Address                        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Options                    |    Padding    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Header Fields

#### Version (4 bits)

- Indicates format of IP header
- Value: 4 (IPv4)
- Enables protocol evolution and coexistence of versions

#### Internet Header Length (IHL, 4 bits)

- Length of header in 32-bit words
- Minimum value: 5 (20 bytes without options)
- Maximum value: 15 (60 bytes with maximum options)
- Points to beginning of data

#### Type of Service (8 bits)

```
Bits 0-2:  Precedence
  111 - Network Control
  110 - Internetwork Control
  101 - CRITIC/ECP
  100 - Flash Override
  011 - Flash
  010 - Immediate
  001 - Priority
  000 - Routine

Bit 3:     Delay (0 = Normal, 1 = Low)
Bit 4:     Throughput (0 = Normal, 1 = High)
Bit 5:     Reliability (0 = Normal, 1 = High)
Bits 6-7:  Reserved for future use
```

**Purpose:** Indicates desired quality of service
**Reality:** Often ignored by routers in practice
**Modern Equivalent:** Replaced by DSCP (Differentiated Services Code Point) in RFC 2474

#### Total Length (16 bits)

- Length of entire datagram (header + data) in octets
- Minimum: 20 bytes (header only)
- Maximum: 65,535 bytes
- Allows determining data length: Total Length - IHL * 4

#### Identification (16 bits)

- Unique identifier assigned by sender
- Used with source address, destination address, and protocol to identify fragments
- All fragments of same datagram carry same identification
- Incremented for each new datagram

#### Flags (3 bits)

```
Bit 0:     Reserved (must be 0)
Bit 1:     Don't Fragment (DF)
           0 = May fragment
           1 = Don't fragment
Bit 2:     More Fragments (MF)
           0 = Last fragment
           1 = More fragments follow
```

**Don't Fragment:** Forces error if fragmentation needed
**More Fragments:** Indicates if more fragments follow

#### Fragment Offset (13 bits)

- Position of fragment in original datagram
- Measured in 8-octet (64-bit) units
- First fragment has offset 0
- Allows reassembly of fragments in correct order

**Example:**
- Original datagram: 3000 bytes
- Fragment 1: offset 0, length 1500 → covers bytes 0-1499
- Fragment 2: offset 185, length 1520 → covers bytes 1480-2999
  - Offset calculation: 1480 / 8 = 185

#### Time to Live (8 bits)

- Maximum time datagram can remain in internet
- Measured in seconds, but typically counts hops
- Decremented by each router that processes datagram
- When reaches 0, datagram discarded
- Prevents packets from looping indefinitely

**Typical Values:**
- 64 (common default)
- 128
- 255 (maximum)

#### Protocol (8 bits)

- Indicates next level protocol used in data portion
- Allows multiplexing different protocols over IP

**Common Values:**
```
1   - ICMP (Internet Control Message Protocol)
6   - TCP (Transmission Control Protocol)
17  - UDP (User Datagram Protocol)
41  - IPv6 (IPv6 encapsulation)
47  - GRE (Generic Routing Encapsulation)
50  - ESP (Encapsulating Security Payload)
51  - AH (Authentication Header)
89  - OSPF (Open Shortest Path First)
```

#### Header Checksum (16 bits)

- Error detection for header only (not data)
- Computed over entire header with checksum field set to 0
- Must be recomputed at each router (due to TTL decrement)

**Algorithm:**
1. Set checksum field to 0
2. Compute one's complement sum of all 16-bit words
3. Take one's complement of result
4. Store in checksum field

**Verification:**
- Sum all 16-bit words including checksum
- If result is all 1s (0xFFFF), header valid

#### Source Address (32 bits)

- IPv4 address of originating host
- Identifies sender of datagram

#### Destination Address (32 bits)

- IPv4 address of destination host
- Identifies intended recipient of datagram

#### Options (variable)

- Variable length field for special processing
- Must be implemented by all IP modules
- Padded with zeros to align header on 32-bit boundary

## IP Addressing

### Address Format

**32-bit addresses** divided into network and host portions:

### Address Classes

**Class A:**
```
0|    Network (7 bits)    |        Host (24 bits)        |
+--+---------------------+--------------------------------+
```
- Range: 1.0.0.0 to 126.255.255.255
- Networks: 128 (2^7, but 0 and 127 reserved)
- Hosts per network: 16,777,214 (2^24 - 2)
- Use: Very large organizations

**Class B:**
```
10|      Network (14 bits)      |    Host (16 bits)    |
+--+---------------------------+----------------------+
```
- Range: 128.0.0.0 to 191.255.255.255
- Networks: 16,384 (2^14)
- Hosts per network: 65,534 (2^16 - 2)
- Use: Medium to large organizations

**Class C:**
```
110|           Network (21 bits)           | Host (8) |
+--+--------------------------------------+----------+
```
- Range: 192.0.0.0 to 223.255.255.255
- Networks: 2,097,152 (2^21)
- Hosts per network: 254 (2^8 - 2)
- Use: Small organizations

**Class D (Multicast):**
```
1110|              Multicast Group (28 bits)            |
+---+---------------------------------------------------+
```
- Range: 224.0.0.0 to 239.255.255.255
- Use: Multicast group addresses

**Class E (Reserved):**
```
1111|              Reserved (28 bits)                   |
+---+---------------------------------------------------+
```
- Range: 240.0.0.0 to 255.255.255.255
- Use: Reserved for future use

### Special Addresses

- **0.0.0.0:** This host on this network
- **255.255.255.255:** Broadcast to all hosts on local network
- **127.0.0.0/8:** Loopback addresses (127.0.0.1 most common)
- **Network ID with host bits all 0:** Network address
- **Network ID with host bits all 1:** Directed broadcast to network

## Fragmentation and Reassembly

### Fragmentation Process

**When Fragmentation Occurs:**
- Datagram larger than network's Maximum Transmission Unit (MTU)
- "Don't Fragment" flag not set

**Fragmentation Steps:**
1. Original datagram divided into multiple fragments
2. Each fragment becomes independent datagram
3. Header copied and modified for each fragment:
   - Total Length set to fragment size
   - More Fragments flag set (except last)
   - Fragment Offset set to position
   - Identification remains same

**Example:**
```
Original Datagram:
  Total Length: 1500 bytes
  IHL: 5 (20 bytes)
  Data: 1480 bytes
  MTU: 576 bytes

Fragment 1:
  Total Length: 576
  Data: 556 bytes (0-555)
  Fragment Offset: 0
  More Fragments: 1

Fragment 2:
  Total Length: 576
  Data: 556 bytes (556-1111)
  Fragment Offset: 69 (556/8)
  More Fragments: 1

Fragment 3:
  Total Length: 388
  Data: 368 bytes (1112-1479)
  Fragment Offset: 139 (1112/8)
  More Fragments: 0
```

### Reassembly Process

**Performed Only at Final Destination:**
- Intermediate routers do not reassemble
- Destination identifies fragments by:
  - Source address
  - Destination address
  - Protocol field
  - Identification field

**Reassembly Steps:**
1. Buffer incoming fragments
2. Use Fragment Offset to position data
3. Check More Fragments flag
4. When all fragments received, combine into original datagram
5. If fragments missing after timeout, discard all fragments

**Reassembly Timeout:**
- Ensures resources not held indefinitely
- Typical value: 60-120 seconds
- ICMP Time Exceeded message may be sent

### Fragmentation Issues

- **Performance:** Additional processing and overhead
- **Loss:** If any fragment lost, entire datagram must be retransmitted
- **Amplification:** Can be exploited for DoS attacks
- **Firewall Problems:** Initial fragment contains port info, subsequent don't

**Modern Practice:**
- Path MTU Discovery (PMTUD) preferred
- Set "Don't Fragment" and discover path MTU
- Send datagrams that don't require fragmentation

## Routing

### Routing Decision Process

**For each datagram, host or router determines:**
1. Is destination on directly connected network?
   - Yes: Send directly to destination
   - No: Forward to appropriate gateway (router)

2. Consult routing table to determine next hop

**Routing Table Entries:**
- Destination network
- Gateway/next hop address
- Interface to use
- Metrics (hop count, cost, etc.)

### Direct vs. Indirect Delivery

**Direct Delivery:**
- Source and destination on same network
- Datagram delivered directly
- Destination address used for physical address lookup (ARP)

**Indirect Delivery:**
- Destination on different network
- Datagram sent to gateway/router
- Router forwards toward destination
- May traverse multiple routers

### Default Gateway

- Catch-all route for destinations not in routing table
- Typically router connected to upstream network
- Enables hosts to reach arbitrary destinations

## IP Options

### Option Format

```
+--------+--------+--------+--------+
| Type   | Length |   Option Data   |
+--------+--------+--------+--------+
```

**Type Field (8 bits):**
```
Bit 0:     Copied flag
           0 = Not copied to all fragments
           1 = Copied to all fragments
Bits 1-2:  Option class
           00 = Control
           01 = Reserved
           10 = Debugging/measurement
           11 = Reserved
Bits 3-7:  Option number
```

### Common Options

#### Record Route (Type 7)

Records route taken by datagram:
```
+--------+--------+--------+---------//--------+
| Type=7 | Length | Pointer|  Route Data       |
+--------+--------+--------+---------//--------+
```
- Each router adds its IP address
- Useful for debugging

#### Source Route (Strict and Loose)

**Strict Source Route (Type 137):**
- Datagram must follow exact path specified
- Lists all routers to traverse
- If route cannot be followed, datagram discarded

**Loose Source Route (Type 131):**
- Datagram must pass through specified routers
- May traverse other routers between specified ones
- More flexible than strict

**Format:**
```
+--------+--------+--------+---------//--------+
| Type   | Length | Pointer|     Route Data    |
+--------+--------+--------+---------//--------+
```

#### Timestamp (Type 68)

Records timestamps along route:
```
+--------+--------+--------+--------+--------+
| Type=68| Length | Pointer|Oflw|Flags|      |
+--------+--------+--------+--------+--------+
|         Timestamp (32 bits)                |
+--------------------------------------------+
```
- Can record timestamp only or timestamp with address
- Useful for measuring delays

## Error Handling

### Checksum Failures

- Datagram with invalid checksum silently discarded
- No error message generated
- Higher layer protocols responsible for detecting loss

### Time to Live Expiration

- When TTL reaches 0, datagram discarded
- ICMP Time Exceeded message sent to source
- Prevents infinite routing loops

### Destination Unreachable

- When destination cannot be reached
- ICMP Destination Unreachable message sent
- Reasons include:
  - Network unreachable
  - Host unreachable
  - Protocol unreachable
  - Port unreachable
  - Fragmentation needed but DF set

### Parameter Problems

- Invalid header field detected
- ICMP Parameter Problem message sent
- Pointer field indicates error location

## Service Model

### Best-Effort Delivery

IP provides **unreliable** service:
- **No Delivery Guarantee:** Datagrams may be lost
- **No Ordering Guarantee:** May arrive out of order
- **No Duplicate Prevention:** May receive duplicates
- **No Corruption Detection:** Data not checksummed (only header)

### Rationale

- **Simplicity:** Minimal complexity in network core
- **Scalability:** Stateless routers scale better
- **Flexibility:** End hosts control reliability mechanisms
- **End-to-End Principle:** Reliability implemented at endpoints (TCP)

## Design Principles

### Datagram Model

- Each packet independent and self-contained
- No connection setup required
- State maintained only at endpoints
- Routers remain simple and stateless

### Layering

- Clear separation from link layer below
- Provides common interface to transport protocols above
- Hides network heterogeneity from upper layers

### Addressing and Routing

- Hierarchical addressing enables routing scalability
- Network portion used for routing decisions
- Host portion for final delivery

### Fragmentation

- Transparent to upper layers
- Handled automatically by IP layer
- Allows operation over diverse link technologies

## Performance Characteristics

### Overhead

- **Minimum Header:** 20 bytes
- **Maximum Header:** 60 bytes (with options)
- **Percentage:** 1.3% for 1500-byte packet, 20% for 100-byte packet

### Processing Costs

- **Checksum Calculation:** O(header_size)
- **Routing Lookup:** O(log n) with efficient structures
- **Fragmentation:** Expensive when needed

### Scalability

- Stateless forwarding enables router scalability
- Hierarchical addressing supports large-scale networks
- Minimal per-packet overhead

## Limitations

### Address Space Exhaustion

- 32-bit addresses provide ~4.3 billion addresses
- Insufficient for modern Internet
- Led to development of IPv6 (RFC 2460)

**Temporary Solutions:**
- CIDR (Classless Inter-Domain Routing)
- NAT (Network Address Translation)
- Private address spaces (RFC 1918)

### Security

- No built-in authentication or encryption
- Source address easily spoofed
- No protection against:
  - Eavesdropping
  - Man-in-the-middle attacks
  - Replay attacks

**Solutions:**
- IPsec (RFC 4301) adds security
- TLS/SSL at transport/application layer

### Fragmentation Vulnerabilities

- Fragment reassembly attacks
- Amplification attacks
- Firewall evasion

### Quality of Service

- Type of Service field largely unused
- No bandwidth reservations
- No strict priority enforcement

**Modern Solutions:**
- IntServ (Integrated Services)
- DiffServ (Differentiated Services)
- MPLS (Multi-Protocol Label Switching)

## Related Protocols

### Internet Control Message Protocol (ICMP)

- Companion protocol to IP (RFC 792)
- Reports errors and provides diagnostic information
- Examples: Ping, Traceroute

### Address Resolution Protocol (ARP)

- Maps IP addresses to link-layer addresses
- Essential for direct delivery on LANs
- RFC 826

### Reverse ARP (RARP)

- Maps link-layer address to IP address
- Used by diskless workstations
- RFC 903
- Largely replaced by BOOTP and DHCP

## Historical Context

- **Published:** September 1981
- **Precursors:** NCP (Network Control Program)
- **Developed By:** DARPA Internet Program
- **Primary Authors:** Jon Postel, et al.
- **Obsoletes:** RFC 760
- **Standard:** Internet Standard (STD 5)

## Evolution

### IPv4 Enhancements

- **RFC 950:** Subnetting
- **RFC 1191:** Path MTU Discovery
- **RFC 1349:** Type of Service enhancements
- **RFC 1812:** Requirements for IPv4 Routers
- **RFC 2474:** Differentiated Services (DSCP)

### Transition to IPv6

- **RFC 2460:** IPv6 Specification
- **128-bit addresses:** Vast address space
- **Simplified header:** Improved processing efficiency
- **Built-in security:** IPsec mandatory
- **Better QoS:** Flow labeling support

## Implementation Considerations

### Host Requirements

- **RFC 1122:** Requirements for Internet Hosts - Communication Layers
- Minimum MTU: 68 bytes
- Must implement fragmentation and reassembly
- Must correctly calculate header checksum
- Must handle TTL properly

### Router Requirements

- **RFC 1812:** Requirements for IP Version 4 Routers
- Forward datagrams not destined for router
- Decrement TTL and verify doesn't reach 0
- Recalculate header checksum
- Fragment if necessary and DF not set
- Update routing tables based on routing protocols

### Performance Optimization

- **Fast Path Processing:** Optimize common case (no options, no fragmentation)
- **Checksum Offload:** Hardware calculation of checksums
- **Routing Cache:** Cache recent routing decisions
- **Parallel Processing:** Process multiple packets concurrently

## Summary

RFC 791 defines the Internet Protocol as a simple, connectionless datagram service that has become the foundation of the Internet. Despite its simplicity and limitations, IP's design has proven remarkably robust and scalable, enabling the Internet's exponential growth.

Key aspects of IP's success:

1. **Simplicity:** Minimal complexity enables efficient implementation and operation
2. **Flexibility:** Best-effort service allows diverse applications and transport protocols
3. **Scalability:** Stateless design and hierarchical addressing support global scale
4. **Interoperability:** Common standard enables heterogeneous network interconnection
5. **Evolvability:** Options mechanism and version field allow protocol evolution

While IPv4 has inherent limitations (address space, security, QoS), it continues to carry the vast majority of Internet traffic. The protocol's fundamental design principles—simplicity, stateless operation, and end-to-end reliability—remain relevant and have influenced subsequent protocol development, including IPv6 and modern transport protocols like QUIC.

IP exemplifies the "end-to-end principle" in network design: keep the network simple and push complexity to the endpoints. This philosophy has enabled the Internet's flexibility, robustness, and unprecedented growth.
