# Changelog

All notable changes to the HarchOS Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-15

### Added

- Initial release of the HarchOS Python SDK
- `HarchOSClient` with both sync and async support
- Sovereign defaults: `region="morocco"`, `sovereignty="strict"`, `carbon_aware=True`
- Authentication module with API key and bearer token support
- Configuration management with named profiles and environment variable overrides
- HTTP transport layer with automatic retry and exponential backoff
- SSE streaming support with async generators
- Resource modules: workloads, models, hubs, energy
- Pydantic v2 models with validators for all resource types
- Comprehensive error hierarchy with typed exceptions
- Carbon budget tracking and green scheduling windows
- Data residency policy enforcement
- GitHub Actions CI/CD workflows
- Full test suite with pytest

### Security

- SSL certificate verification enabled by default
- API key validation with format enforcement
- Token expiry detection and automatic fallback
