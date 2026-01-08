# Security Notes (Research Prototype)

## Scope
HRPO-X is a research prototype. This repository does not provide network
services, authentication, or production deployment tooling.

## Supported Versions
There are no supported production versions. Use at your own risk.

## Reporting
If you find a security issue in this repository, open a private issue or
contact the maintainer directly.

## What Exists (and what does not)
- In-memory, single-process hash coordination (simulated)
- No authentication or authorization
- No audit logging
- No network services or exposed ports in the codebase

## Recommendations for Experiments
- Run in isolated environments
- Do not use real secrets or regulated data
- Review dependencies and pin versions for your environment

## Removed Claims
Any prior references to audits, SOC 2, ISO 27001, or production-grade
Byzantine fault tolerance do not apply to this prototype.
