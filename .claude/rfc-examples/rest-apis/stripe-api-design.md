# Stripe API Design and Patterns

**Source:** Stripe, Inc.
**URL:** https://docs.stripe.com/api and https://stripe.com/blog/payment-api-design
**Type:** Production API Example
**Notable For:** Developer experience, API evolution, backward compatibility

## Overview

Stripe's API is widely regarded as one of the best-designed REST APIs in the industry. This document captures Stripe's design principles, patterns, and evolution strategies based on over 10 years of payment API development.

## Core Design Principles

### Developer Experience First

**Guiding Philosophy: "Seven lines of code"**

The goal is to make complex payment operations feel simple and intuitive:

```ruby
# Original Stripe charge creation (simplified)
Stripe::Charge.create(
  amount: 2000,
  currency: 'usd',
  source: 'tok_visa',
  description: 'Example charge'
)
```

**Key Tenets:**
1. Make the simple case simple
2. Gradually reveal complexity
3. Provide clear, actionable errors
4. Minimize integration time

### API Design Philosophy

From "Stripe's payments APIs: The first 10 years":

> "Abstracting away the complexity of payments has driven the evolution of Stripe's APIs over the last decade."

**Core Beliefs:**
- Great APIs solve complex problems simply
- Consistency builds trust
- Documentation is as important as code
- Evolution must preserve compatibility

## REST Principles

### Core Characteristics

**Request Format:**
- Accepts form-encoded request bodies (`application/x-www-form-urlencoded`)
- Alternative: JSON for complex nested structures

**Response Format:**
- Returns JSON-encoded responses (`application/json`)

**HTTP Conventions:**
- Standard HTTP response codes
- Standard HTTP verbs (GET, POST, DELETE)
- Idempotent operations where appropriate

**Base URL:**
```
https://api.stripe.com
```

### No Bulk Operations

> "The Stripe API doesn't support bulk updates and works on only one object per request."

**Rationale:**
- Simplifies error handling
- Clearer audit trails
- Easier to reason about state changes
- Better fits transactional payment operations

**Alternative Approaches:**
- Use webhooks for async bulk operations
- Client-side iteration for batch needs
- Consider rate limits when iterating

## Object-Based Architecture

**Core Principle:**

> "Everything in your Stripe account is an object."

### Resource Types

Common Stripe objects:
- **PaymentIntent**: Represents intent to collect payment
- **Charge**: Record of payment attempt
- **Customer**: Represents a customer
- **PaymentMethod**: Stored payment details
- **Subscription**: Recurring payment schedule
- **Invoice**: Statement of amounts owed
- **Balance**: Account balance
- **Event**: Webhook event

### Object Structure

**Common Fields:**
```json
{
  "id": "pi_1234567890",
  "object": "payment_intent",
  "created": 1234567890,
  "livemode": false,
  "metadata": {},
  ...
}
```

**Standard Attributes:**
- `id`: Unique identifier
- `object`: Type of object
- `created`: Unix timestamp
- `livemode`: Test vs production mode
- `metadata`: Custom key-value data

## API Evolution: PaymentIntents Example

### The Problem: Payment Method Diversity

Original Stripe API designed around card payments:
```ruby
# Simple card charge
charge = Stripe::Charge.create(
  amount: 1000,
  currency: 'usd',
  source: card_token
)
```

**Challenges:**
- Different payment methods have different flows
- Some require user actions (3D Secure, bank redirects)
- Each method added parameters to Charge object
- "Product debt" accumulated through patches

### The Solution: PaymentIntents API

**New abstraction layer:**
```ruby
# Create PaymentIntent
payment_intent = Stripe::PaymentIntent.create(
  amount: 1000,
  currency: 'usd',
  payment_method_types: ['card']
)

# Confirm with payment method
payment_intent.confirm(
  payment_method: 'pm_card_visa'
)
```

**Key Design Decisions:**

1. **Clear State Machine:**
   - `requires_payment_method`
   - `requires_confirmation`
   - `requires_action` (for 3D Secure, etc.)
   - `processing`
   - `succeeded`
   - `canceled`

2. **Separation of Concerns:**
   - Intent creation separate from confirmation
   - Payment method selection decoupled from flow
   - Handle async operations gracefully

3. **Backward Compatibility:**
   - PaymentIntents create Charges internally
   - Existing integrations continue working
   - Gradual migration path provided

### Lessons from Evolution

**Avoid Product Debt:**
> "Like tech debt, product debt accumulates gradually in API products."

**When to Redesign:**
- When parameters become unwieldy
- When special cases proliferate
- When users struggle with mental model
- When new features require contortions

**Migration Strategy:**
- Layer new APIs over old
- Maintain compatibility
- Provide migration tools
- Don't force rewrites

## Versioning Strategy

### Account-Based Versioning

**Unique Approach:**
- Version pinned to Stripe account, not per-request
- Upgrade version in dashboard
- Test changes with API version parameter

**Setting Version:**
```bash
# Request-level override
curl https://api.stripe.com/v1/charges \
  -H "Stripe-Version: 2023-10-16"
```

**Benefits:**
- No version in URL path
- Easy to test new versions
- Gradual rollout across accounts
- Rollback capability

### Version Changes

**Non-Breaking Changes:**
- New endpoints
- New fields in responses
- New optional parameters
- New event types

**Breaking Changes (trigger new version):**
- Removing endpoints
- Removing response fields
- Changing field types
- Changing endpoint behavior
- New required parameters

### Changelog and Migration

**Documentation:**
- Detailed changelog for each version
- Migration guides
- Code examples showing before/after
- Timeline for version deprecation

## Error Handling

### Error Response Structure

```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "Amount must be at least $0.50 usd",
    "param": "amount",
    "code": "amount_too_small"
  }
}
```

### Error Types

- `api_error`: Stripe server error
- `api_connection_error`: Network communication failure
- `authentication_error`: Authentication failed
- `card_error`: Card declined or invalid
- `idempotency_error`: Idempotency key reused inappropriately
- `invalid_request_error`: Invalid parameters
- `rate_limit_error`: Too many requests

### HTTP Status Codes

- `200`: Success
- `400`: Bad request (invalid parameters)
- `401`: Authentication failed
- `402`: Request failed
- `403`: Forbidden
- `404`: Resource not found
- `409`: Conflict (e.g., idempotency)
- `429`: Rate limit exceeded
- `500`, `502`, `503`, `504`: Server errors

### Error Handling Best Practices

```python
import stripe

try:
    charge = stripe.Charge.create(...)
except stripe.error.CardError as e:
    # Card was declined
    body = e.json_body
    err = body.get('error', {})
    print(f"Card declined: {err.get('message')}")
except stripe.error.RateLimitError:
    # Rate limit exceeded
    print("Rate limit exceeded, retry later")
except stripe.error.InvalidRequestError as e:
    # Invalid parameters
    print(f"Invalid request: {e.user_message}")
except stripe.error.AuthenticationError:
    # Authentication failed
    print("Authentication failed")
except stripe.error.StripeError as e:
    # Generic Stripe error
    print(f"Stripe error: {e}")
```

## Idempotency

### Idempotency Keys

**Purpose:** Prevent duplicate operations due to network issues

**Implementation:**
```bash
curl https://api.stripe.com/v1/charges \
  -u sk_test_key: \
  -H "Idempotency-Key: random_unique_string" \
  -d amount=1000 \
  -d currency=usd
```

**Behavior:**
- Same key within 24 hours returns cached result
- Different parameters with same key returns error
- Automatically handle retry scenarios

### API v2 Idempotency Improvements

**Enhanced behavior:**
- If first request succeeded: return updated response (skip making new changes)
- If first request failed: re-execute and return new response

**Benefits:**
- Safer retries
- Better handling of network issues
- Clearer retry semantics

## Pagination

### List Endpoints

**Request:**
```bash
curl https://api.stripe.com/v1/charges \
  -u sk_test_key: \
  -d limit=10 \
  -d starting_after=ch_1234567890
```

**Response:**
```json
{
  "object": "list",
  "data": [...],
  "has_more": true,
  "url": "/v1/charges"
}
```

### Pagination Parameters

- `limit`: Number of results (default 10, max 100)
- `starting_after`: Cursor for forward pagination
- `ending_before`: Cursor for backward pagination

### Auto-Pagination in SDKs

```python
# Automatic pagination
for charge in stripe.Charge.auto_paging_iter(limit=100):
    process(charge)
```

## Expansion (Field Selection)

### Expandable Fields

**Default response (ID only):**
```json
{
  "id": "ch_1234567890",
  "customer": "cus_1234567890"
}
```

**Expanded response:**
```bash
curl https://api.stripe.com/v1/charges/ch_1234567890 \
  -u sk_test_key: \
  -d "expand[]"=customer
```

```json
{
  "id": "ch_1234567890",
  "customer": {
    "id": "cus_1234567890",
    "email": "customer@example.com",
    ...
  }
}
```

### Nested Expansion

```bash
-d "expand[]"=customer \
-d "expand[]"=customer.default_source
```

**Benefits:**
- Reduce API calls
- Fetch related data efficiently
- Control response size

## Metadata

### Custom Key-Value Storage

**Adding metadata:**
```python
charge = stripe.Charge.create(
  amount=1000,
  currency='usd',
  source='tok_visa',
  metadata={
    'order_id': '12345',
    'customer_name': 'John Doe'
  }
)
```

**Characteristics:**
- Up to 50 keys
- Keys up to 40 characters
- Values up to 500 characters
- Searchable in dashboard
- Included in webhooks

**Use Cases:**
- Link to internal IDs
- Store contextual information
- Track custom attributes
- Aid in reconciliation

## Webhooks

### Event-Driven Integration

**Webhook Event Structure:**
```json
{
  "id": "evt_1234567890",
  "object": "event",
  "type": "charge.succeeded",
  "data": {
    "object": {
      "id": "ch_1234567890",
      ...
    }
  },
  "created": 1234567890
}
```

### Common Event Types

- `charge.succeeded`: Payment succeeded
- `charge.failed`: Payment failed
- `payment_intent.succeeded`: PaymentIntent succeeded
- `customer.created`: Customer created
- `invoice.payment_succeeded`: Invoice paid
- `subscription.created`: Subscription started

### Webhook Best Practices

```python
import stripe

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    # Handle event
    if event['type'] == 'charge.succeeded':
        charge = event['data']['object']
        handle_successful_charge(charge)

    return '', 200
```

**Security:**
- Verify webhook signatures
- Use HTTPS endpoints
- Implement idempotent handlers
- Return 200 quickly (process async)

## API Design Patterns

### Polymorphic Resources

**Example: payment_method_details**

```json
{
  "payment_method_details": {
    "type": "card",
    "card": {
      "brand": "visa",
      "last4": "4242",
      ...
    }
  }
}
```

**For different payment method:**
```json
{
  "payment_method_details": {
    "type": "sepa_debit",
    "sepa_debit": {
      "country": "DE",
      "last4": "3000",
      ...
    }
  }
}
```

**Benefits:**
- Type-safe structure
- Extensible to new payment methods
- Clear which fields are relevant

### State Machines

**Clear state transitions:**
```
PaymentIntent States:
requires_payment_method → requires_confirmation
                       ↓
                  requires_action
                       ↓
                   processing
                       ↓
                   succeeded
```

**Benefits:**
- Predictable behavior
- Clear error states
- Easier to reason about
- Self-documenting flow

### Nested Resources

**Parent-child relationships:**
```
/v1/customers/:customer_id/sources
/v1/invoices/:invoice_id/lines
/v1/subscriptions/:subscription_id/items
```

## Test Mode

### Separate Test and Live Modes

**API Keys:**
- `sk_test_...`: Test mode
- `sk_live_...`: Production mode

**Benefits:**
- Safe testing environment
- Identical behavior to production
- Special test card numbers
- No real money involved

**Test Cards:**
```
4242424242424242  # Succeeds
4000000000000002  # Declined
4000002500003155  # Requires 3D Secure
```

## Developer Tools

### Stripe CLI

**Local webhook testing:**
```bash
stripe listen --forward-to localhost:3000/webhook
stripe trigger payment_intent.succeeded
```

**Log tailing:**
```bash
stripe logs tail
```

### Documentation Quality

**Key Features:**
- Interactive API reference
- Code examples in 8+ languages
- Working examples with test data
- Searchable and well-organized
- Changelog for all versions

## Key Takeaways from Stripe's Evolution

### Design Principles

1. **Simplicity First**: Make common cases simple, allow complexity when needed
2. **Predictable State**: Use clear state machines for complex flows
3. **Extensibility**: Design for future payment methods and features
4. **Backward Compatibility**: Never break existing integrations
5. **Developer Experience**: Treat documentation and tooling as first-class

### Evolution Strategy

1. **Layer, Don't Replace**: New APIs wrap old ones
2. **Gradual Migration**: Provide migration paths, not forced upgrades
3. **Learn from Users**: Real integrations inform design decisions
4. **Question Assumptions**: Periodically redesign core abstractions
5. **Move Quickly**: Make decisions fast, iterate based on feedback

### API Architecture

1. **Object-Oriented**: Every resource is a well-defined object
2. **RESTful**: Standard HTTP methods and status codes
3. **Idempotent**: Safe retries with idempotency keys
4. **Event-Driven**: Webhooks for async operations
5. **Flexible**: Metadata, expansion, and customization options

## References

- API Reference: https://docs.stripe.com/api
- API Evolution Blog: https://stripe.com/blog/payment-api-design
- API Changelog: https://docs.stripe.com/upgrades
- Stripe CLI: https://stripe.com/docs/stripe-cli

---

**Key Takeaways:**

1. Developer experience is paramount - optimize for "seven lines of code"
2. Gradual complexity revelation: simple by default, powerful when needed
3. Backward compatibility through layering, not breaking changes
4. Clear state machines for complex multi-step operations
5. Comprehensive error handling with actionable messages
6. Account-based versioning enables safe, gradual upgrades
7. Idempotency keys prevent duplicate operations
8. Webhooks for async operations and event-driven architecture
9. Strong typing through polymorphic objects
10. Excellent documentation and developer tooling as product features
