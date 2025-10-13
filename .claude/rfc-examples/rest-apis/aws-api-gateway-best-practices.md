# AWS API Gateway Best Practices

**Source:** Amazon Web Services
**URL:** https://docs.aws.amazon.com/apigateway/latest/developerguide/
**Type:** Cloud Platform Best Practices
**Focus:** Security, Architecture, and Operations

## Overview

AWS API Gateway provides a comprehensive service for creating, publishing, maintaining, monitoring, and securing REST, HTTP, and WebSocket APIs. These best practices cover security, architecture, and operational considerations for building production-grade APIs on AWS.

## API Types

AWS API Gateway supports three API types:

### REST API
- Full-featured API with resource-oriented design
- Support for request/response transformation
- Advanced features (caching, API keys, usage plans)

### HTTP API
- Lower-cost, lower-latency alternative
- Simpler feature set
- Better for modern microservices

### WebSocket API
- Bidirectional communication
- Real-time applications
- Persistent connections

## Security Best Practices

### Authentication and Authorization

#### IAM Policies

**Principle: Implement Least Privilege Access**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "apigateway:GET",
        "apigateway:POST"
      ],
      "Resource": "arn:aws:apigateway:region::/restapis/*/stages/*/methods/*"
    }
  ]
}
```

**Best Practices:**
- Grant minimum permissions needed
- Use resource-specific policies
- Regularly audit IAM permissions
- Use IAM roles instead of users when possible

#### Lambda Authorizers

**Custom authorization logic:**

```javascript
exports.handler = async (event) => {
  const token = event.authorizationToken;

  // Validate token
  if (isValidToken(token)) {
    return generatePolicy('user', 'Allow', event.methodArn);
  }

  return generatePolicy('user', 'Deny', event.methodArn);
};
```

**Use cases:**
- OAuth 2.0 tokens
- SAML assertions
- Custom authentication schemes

#### Cognito Authorizers

**Integration with AWS Cognito:**
- User pool authentication
- Identity federation
- Built-in user management

```yaml
Resources:
  ApiGatewayAuthorizer:
    Type: AWS::ApiGateway::Authorizer
    Properties:
      Type: COGNITO_USER_POOLS
      IdentitySource: method.request.header.Authorization
      ProviderARNs:
        - !GetAtt UserPool.Arn
```

#### JWT Authorizers (HTTP APIs)

**Token-based authentication:**

```yaml
Authorizers:
  JWTAuthorizer:
    IdentitySource: $request.header.Authorization
    JwtConfiguration:
      Audience:
        - api-audience
      Issuer: https://cognito-idp.region.amazonaws.com/userPoolId
```

### API Keys and Usage Plans

**Important Limitations:**

> "Don't use API keys for authentication or authorization to control access to your APIs."

**Appropriate Uses:**
- Rate limiting by client
- Usage tracking
- Basic access control for internal APIs

**Anti-patterns:**
- Using as primary authentication
- Sharing across multiple clients
- Embedding in public applications

**Best Practice:**
```yaml
ApiKey:
  Type: AWS::ApiGateway::ApiKey
  Properties:
    Name: partner-api-key
    Description: API key for partner integration
    Enabled: true

UsagePlan:
  Type: AWS::ApiGateway::UsagePlan
  Properties:
    Throttle:
      RateLimit: 1000
      BurstLimit: 2000
    Quota:
      Limit: 50000
      Period: DAY
```

### Request Validation

**Schema-based validation:**

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "username": {
      "type": "string",
      "minLength": 3,
      "maxLength": 20
    },
    "email": {
      "type": "string",
      "format": "email"
    }
  },
  "required": ["username", "email"]
}
```

**Benefits:**
- Reject invalid requests early
- Reduce backend load
- Improve error messages
- Prevent injection attacks

### Private APIs and VPC Endpoints

**Private API Architecture:**

```
Client (VPC) → VPC Endpoint → Private API Gateway → Lambda/Service
```

**Security Benefits:**
- Traffic never leaves AWS network
- No public internet exposure
- Enhanced DDoS protection
- VPC security group controls

**Configuration:**
```yaml
RestApi:
  Type: AWS::ApiGateway::RestApi
  Properties:
    Name: private-api
    EndpointConfiguration:
      Types:
        - PRIVATE
    Policy:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal: '*'
          Action: 'execute-api:Invoke'
          Resource: '*'
          Condition:
            StringEquals:
              'aws:sourceVpce': !Ref VpcEndpoint
```

**Best Practices:**
- Use for internal APIs
- Implement resource policies
- Use VPC security groups
- Consider AWS PrivateLink

## Architecture Best Practices

### Resource Design

**RESTful Conventions:**

```
GET    /users              # List users
GET    /users/{id}         # Get specific user
POST   /users              # Create user
PUT    /users/{id}         # Update user
DELETE /users/{id}         # Delete user

GET    /users/{id}/posts   # Nested resources
```

**Best Practices:**
- Use nouns for resources
- Use HTTP methods for actions
- Support nested resources
- Version your APIs

### Integration Types

#### Lambda Proxy Integration

**Simplest integration:**
```javascript
exports.handler = async (event) => {
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message: 'Success' })
  };
};
```

**Benefits:**
- Full control over response
- Access to all request details
- Simplified development

#### HTTP Integration

**Direct HTTP backend:**
```yaml
Integration:
  Type: HTTP
  IntegrationHttpMethod: POST
  Uri: https://backend.example.com/api
```

#### AWS Service Integration

**Direct AWS service calls:**
```yaml
Integration:
  Type: AWS
  IntegrationHttpMethod: POST
  Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:dynamodb:action/PutItem'
  Credentials: !GetAtt ApiGatewayRole.Arn
```

### Throttling and Rate Limiting

**Account-Level Limits:**
- 10,000 requests per second (RPS) by default
- 5,000 burst capacity

**Stage-Level Throttling:**
```yaml
StageSettings:
  ThrottlingRateLimit: 1000
  ThrottlingBurstLimit: 2000
```

**Method-Level Throttling:**
```yaml
MethodSettings:
  - ResourcePath: '/users'
    HttpMethod: 'POST'
    ThrottlingRateLimit: 100
    ThrottlingBurstLimit: 200
```

**Usage Plan Throttling:**
```yaml
UsagePlan:
  Properties:
    Throttle:
      RateLimit: 500
      BurstLimit: 1000
```

**Best Practices:**
- Set appropriate limits per endpoint
- Use usage plans for API keys
- Monitor throttle metrics
- Implement retry with exponential backoff

### Caching

**Stage-Level Caching:**
```yaml
CacheClusterEnabled: true
CacheClusterSize: '0.5'  # GB
MethodSettings:
  - ResourcePath: '/users'
    HttpMethod: 'GET'
    CachingEnabled: true
    CacheTtlInSeconds: 300
```

**Cache Key Parameters:**
```yaml
RequestParameters:
  method.request.querystring.page: true
  method.request.querystring.limit: true
CacheKeyParameters:
  - method.request.querystring.page
  - method.request.querystring.limit
```

**Best Practices:**
- Cache GET requests only
- Set appropriate TTL
- Use cache key parameters
- Implement cache invalidation
- Monitor cache hit rates

### Error Handling

**Gateway Responses:**
```yaml
GatewayResponses:
  - ResponseType: UNAUTHORIZED
    StatusCode: 401
    ResponseTemplates:
      application/json: |
        {
          "error": "Unauthorized",
          "message": "$context.error.messageString"
        }
```

**Custom Error Handling:**
```javascript
exports.handler = async (event) => {
  try {
    // Process request
    return {
      statusCode: 200,
      body: JSON.stringify(result)
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Internal Server Error',
        message: error.message,
        requestId: event.requestContext.requestId
      })
    };
  }
};
```

## Monitoring and Logging

### CloudWatch Metrics

**Standard Metrics:**
- **Count**: Total API requests
- **4XXError**: Client errors
- **5XXError**: Server errors
- **Latency**: Time to process request
- **IntegrationLatency**: Backend processing time
- **CacheHitCount**: Cache hits
- **CacheMissCount**: Cache misses

**Custom Metrics:**
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='CustomAPI',
    MetricData=[
        {
            'MetricName': 'BusinessMetric',
            'Value': 1,
            'Unit': 'Count'
        }
    ]
)
```

### CloudWatch Logs

**Enable Access Logging:**
```yaml
AccessLogSetting:
  DestinationArn: !GetAtt ApiAccessLogGroup.Arn
  Format: |
    {
      "requestId": "$context.requestId",
      "ip": "$context.identity.sourceIp",
      "caller": "$context.identity.caller",
      "user": "$context.identity.user",
      "requestTime": "$context.requestTime",
      "httpMethod": "$context.httpMethod",
      "resourcePath": "$context.resourcePath",
      "status": "$context.status",
      "protocol": "$context.protocol",
      "responseLength": "$context.responseLength"
    }
```

**Enable Execution Logging:**
```yaml
MethodSettings:
  - LoggingLevel: INFO
    DataTraceEnabled: true
    MetricsEnabled: true
```

**Log Levels:**
- **OFF**: No logging
- **ERROR**: Log errors only
- **INFO**: Log all requests

### CloudWatch Alarms

**Error Rate Alarm:**
```yaml
ErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: 5XXError
    Namespace: AWS/ApiGateway
    Statistic: Sum
    Period: 60
    EvaluationPeriods: 2
    Threshold: 10
    ComparisonOperator: GreaterThanThreshold
```

**Latency Alarm:**
```yaml
LatencyAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: Latency
    Namespace: AWS/ApiGateway
    Statistic: Average
    Period: 300
    Threshold: 1000
    ComparisonOperator: GreaterThanThreshold
```

### AWS CloudTrail

**API Management Audit Trail:**
```yaml
Trail:
  Type: AWS::CloudTrail::Trail
  Properties:
    IsLogging: true
    IncludeGlobalServiceEvents: true
    EventSelectors:
      - DataResources:
          - Type: AWS::ApiGateway::RestApi
            Values:
              - !Sub '${RestApi}/stages/${Stage}'
```

**Logged Events:**
- API creation/deletion
- Stage deployments
- Method configuration changes
- Authorizer modifications
- Resource policy updates

## Operational Best Practices

### Deployment Strategies

#### Canary Deployments

**Gradual rollout:**
```yaml
Deployment:
  Type: AWS::ApiGateway::Deployment
  Properties:
    StageDescription:
      CanarySettings:
        PercentTraffic: 10
        UseStageCache: false
```

**Best Practices:**
- Start with small percentage (5-10%)
- Monitor metrics closely
- Promote or rollback based on results
- Use stage variables for configuration

#### Blue/Green Deployments

**Zero-downtime deployments:**
```yaml
BlueStage:
  Type: AWS::ApiGateway::Stage
  Properties:
    StageName: blue

GreenStage:
  Type: AWS::ApiGateway::Stage
  Properties:
    StageName: green
```

**Process:**
1. Deploy to green stage
2. Test green stage
3. Switch DNS/client to green
4. Keep blue for rollback

### Versioning

**URL Path Versioning:**
```
/v1/users
/v2/users
```

**Best Practices:**
- Version in URL path
- Maintain backward compatibility
- Deprecate old versions gradually
- Document version differences

### Cost Optimization

**Strategies:**
- Use HTTP APIs for simpler use cases (60% cheaper)
- Enable caching for repeated requests
- Optimize Lambda function execution time
- Use appropriate throttling limits
- Consider AWS Budgets for monitoring

### Security Monitoring with AWS Security Hub

**Best Practice Checks:**
- API Gateway REST API logging enabled
- API Gateway REST API cache encryption enabled
- API Gateway REST API execution logging enabled
- API Gateway REST and WebSocket API WAF enabled
- API Gateway REST API public endpoints configured

## Common Patterns

### Authentication Flow

```
Client → API Gateway (JWT Authorizer) → Lambda → DynamoDB
         ↓ (valid token)
         Cached authorization decision
```

### Microservices Architecture

```
API Gateway
├── /users → Lambda (Users Service)
├── /orders → Lambda (Orders Service)
└── /products → Lambda (Products Service)
```

### Backend Integration

```
API Gateway
├── Lambda Proxy (Business Logic)
├── HTTP Proxy (External API)
└── AWS Service (DynamoDB Direct)
```

## Security Checklist

- [ ] Use IAM policies with least privilege
- [ ] Implement appropriate authorizer (Lambda, Cognito, JWT)
- [ ] Don't use API keys for authentication
- [ ] Enable request validation
- [ ] Use private APIs for internal services
- [ ] Implement throttling and rate limiting
- [ ] Enable access logging
- [ ] Enable AWS CloudTrail
- [ ] Use AWS WAF for protection
- [ ] Encrypt sensitive data
- [ ] Regular security audits with Security Hub
- [ ] Monitor for anomalous behavior
- [ ] Implement proper error handling

## References

- Security Best Practices: https://docs.aws.amazon.com/apigateway/latest/developerguide/security-best-practices.html
- Private APIs Best Practices: https://docs.aws.amazon.com/whitepapers/latest/best-practices-api-gateway-private-apis-integration/
- Developer Guide: https://docs.aws.amazon.com/apigateway/latest/developerguide/

---

**Key Takeaways:**

1. Security is paramount - use proper authentication and authorization
2. API keys are for rate limiting, not authentication
3. Private APIs provide enhanced security for internal services
4. Monitoring and logging are essential for operations
5. Implement appropriate throttling to protect backend systems
6. Use caching to improve performance and reduce costs
7. Deploy safely with canary or blue/green strategies
8. Regular security audits with AWS Security Hub
