# UTCP v1.0 Specification Reference

## Manual Top-Level Structure

```json
{
  "manual_version": "1.0.0",
  "utcp_version": "1.0.2",
  "tools": [
    {
      "name": "service_name.resource_action",
      "description": "Clear explanation of what the tool does, when to call it, and side effects.",
      "tags": ["resource_tag"],
      "inputs": {
        "type": "object",
        "properties": {
          "user_id": { "type": "string", "description": "Target user ID" }
        },
        "required": ["user_id"]
      },
      "outputs": {
        "type": "object",
        "description": "JSON response from endpoint"
      },
      "tool_call_template": {
        "name": "service_name.resource_action",
        "call_template_type": "http",
        "url": "https://api.example.com/users/{user_id}",
        "http_method": "GET",
        "content_type": "application/json",
        "allowed_communication_protocols": ["http"],
        "auth": {
          "auth_type": "api_key",
          "api_key": "Bearer ${service_name__API_KEY}",
          "var_name": "Authorization",
          "location": "header"
        }
      }
    }
  ]
}
```

## Expert Namespacing Rules

1. **Tool Names**: Always namespaced as `<manual_name>.<resource>_<action>` to prevent collisions across multiple tool providers.
2. **Variable Namespacing**: Any environment or secret variable must be prefixed with `<manual_name>__` (double underscore) so clients isolate credentials per manual.
3. **Protocol Restriction**: Must specify `allowed_communication_protocols: ["http"]` to block unauthorized protocol escalation (e.g. calling CLI tools from HTTP manual).
