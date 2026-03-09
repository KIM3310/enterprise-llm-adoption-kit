## Summary

<!-- One-paragraph description of what this PR does and why. -->

## Changes

<!-- Bulleted list of the key changes in this PR. -->

-

## Type of Change

<!-- Check the relevant box. -->

- [ ] Bug fix (non-breaking change that resolves an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Refactoring (no functional changes, no API changes)
- [ ] Documentation update
- [ ] Infrastructure / CI/CD change

## Testing

<!-- Describe how you tested these changes. -->

- [ ] Existing tests pass (`pytest`)
- [ ] New tests added for changed functionality
- [ ] Manual testing performed (describe below)

## Governance Checklist

<!-- For changes that touch the request pipeline or data layer. -->

- [ ] RBAC enforcement is preserved (no role escalation paths introduced)
- [ ] Prompt injection detection still covers the modified code paths
- [ ] PII redaction applies before any new persistence or external API call
- [ ] Audit logging captures the new event types with hashed payloads
- [ ] Snowflake / Databricks adapters remain env-var gated (no-op when unconfigured)

## Deployment Notes

<!-- Any special steps required for deployment (env vars, migrations, etc.). Leave blank if none. -->

## Related Issues

<!-- Link related issues: Fixes #123, Relates to #456 -->
