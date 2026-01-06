# Security Policy

## [#] Overview

HRPO-X is committed to maintaining the highest security standards for production AI systems. This document outlines our security policies, vulnerability reporting process, and best practices.

---

## [!] Supported Versions

We actively support the following versions with security updates:

| Version | Status | Security Support | End of Life |
|---------|--------|-----------------|-------------|
| 2.2.f   | [+] Current | Full support | N/A |
| 2.1.x   | [*] Maintenance | Critical only | 2026-06-01 |
| 2.0.x   | [-] End of Life | None | 2025-12-31 |
| < 2.0   | [-] Unsupported | None | Expired |

---

## [!] Reporting a Vulnerability

### How to Report

If you discover a security vulnerability in HRPO-X, please report it responsibly:

1. **DO NOT** open a public GitHub issue
2. **Email**: security@flamehaven.io with subject "HRPO-X Security"
3. **Encrypt** (optional): Use our PGP key (see below)
4. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if available)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Fix Development**: Within 30 days (critical), 90 days (high)
- **Public Disclosure**: After fix is released + 14 days

### Severity Levels

- **Critical (CVSS 9.0-10.0)**: Immediate response, 24-hour patch
- **High (CVSS 7.0-8.9)**: Priority response, 30-day patch
- **Medium (CVSS 4.0-6.9)**: Standard response, 90-day patch
- **Low (CVSS 0.1-3.9)**: Next release cycle

---

## [#] Security Features

### Byzantine Fault Tolerance

HRPO-X includes production-grade Byzantine fault tolerance:

- **Hash-based validation** with ACK tracking
- **Grace period** for network partitions
- **Automatic worker recovery**
- **Tamper detection** for policy weights

**Configuration**: See `config/base_config.yaml` → `network.broadcast_timeout`

### Distributional Safety Validation

4-metric ghost mode ensures safe model deployment:

1. **Error Rate** < 1%
2. **Reward KL Divergence** < 0.1
3. **Length Variance** 0.5-2.0x
4. **Delimiter Stability** |diff| < 0.5

**Statistical Confidence**: 99.9% (bootstrap CI with 1000 iterations)

### Model Integrity

- **Hash locking**: Golden Core (Eq 3/4/6) is immutable
- **Checksum verification**: All model weights validated
- **Audit trail**: Complete training history logged

---

## [T] Security Best Practices

### Deployment

```yaml
# Production deployment security checklist
deployment:
  - [ ] Enable TLS for all network communication
  - [ ] Use Redis AUTH for hash broadcast
  - [ ] Restrict network access to training workers
  - [ ] Enable audit logging for all operations
  - [ ] Use separate credentials per environment
  - [ ] Implement rate limiting on inference API
  - [ ] Enable model checksum verification
  - [ ] Configure firewall rules for worker nodes
```

### Configuration

```yaml
# Secure configuration template
security:
  network:
    tls_enabled: true
    redis_auth: true
    worker_auth_token: "${WORKER_AUTH_TOKEN}"  # Use env vars
    broadcast_timeout: 5.0
    
  validation:
    ghost_mode_enabled: true
    min_samples: 250
    confidence: 0.99
    
  monitoring:
    audit_log_enabled: true
    anomaly_detection: true
    alert_on_suspicious_activity: true
```

### Data Privacy

- **Training Data**: Never log sensitive training samples
- **Model Outputs**: Sanitize outputs before logging
- **Metrics**: Aggregate statistics only, no raw data
- **Redis**: Use in-memory only, no disk persistence for sensitive data

### Access Control

```bash
# Recommended file permissions
chmod 600 config/*.yaml      # Config files: owner read/write only
chmod 700 scripts/*.sh       # Scripts: owner execute only
chmod 644 *.py               # Source: world-readable
chmod 600 .env               # Secrets: owner read/write only
```

---

## [B] Known Security Considerations

### Importance Sampling (IS)

**Risk**: Stale policy trajectories could be exploited

**Mitigation**:
- Maximum lag k=3 enforced
- KL divergence rejection threshold (max_kl=0.01)
- Grace period limited to 1 trajectory per worker
- Exponential backoff for persistent failures

### Ghost Mode Traffic Splitting

**Risk**: Sensitive data might reach untested candidate model

**Mitigation**:
- Traffic limited to 25% maximum
- Statistical validation before full rollout
- Automatic rollback on any metric failure
- Audit log of all ghost mode sessions

### Distributed Training

**Risk**: Worker compromise could poison training

**Mitigation**:
- Byzantine fault tolerance with ACK tracking
- Policy hash validation on every trajectory
- Anomaly detection on worker metrics
- Automatic worker quarantine on suspicious behavior

---

## [L] Compliance & Standards

### Standards We Follow

- **OWASP Top 10**: Web application security
- **CWE/SANS Top 25**: Software security weaknesses
- **NIST Cybersecurity Framework**: Risk management
- **ISO 27001**: Information security management

### Certifications

- [ ] SOC 2 Type II (In Progress)
- [ ] ISO 27001 (Planned Q2 2026)
- [ ] GDPR Compliance (EU deployments)

---

## [>] Security Audits

### Internal Audits

- **Frequency**: Quarterly
- **Scope**: Code, configuration, dependencies
- **Tools**: Bandit, Safety, Trivy, Snyk

### External Audits

- **Last Audit**: 2025-12-15
- **Auditor**: [To be announced]
- **Report**: Available upon request

### Dependency Scanning

```bash
# Run security checks
pip install safety bandit

# Check dependencies
safety check -r requirements.txt

# Check code
bandit -r . -ll
```

---

## [*] Incident Response

### Severity Classification

**P0 - Critical**:
- Data breach or unauthorized access
- Model poisoning or tampering
- System-wide service disruption

**P1 - High**:
- Partial data exposure
- DoS on critical components
- Privilege escalation

**P2 - Medium**:
- Information disclosure (non-sensitive)
- Performance degradation
- Configuration vulnerabilities

**P3 - Low**:
- Documentation issues
- Minor bugs with security implications

### Response Process

1. **Detection**: Automated monitoring + manual reports
2. **Triage**: Severity assessment within 1 hour
3. **Containment**: Isolate affected systems immediately
4. **Investigation**: Root cause analysis within 24 hours
5. **Remediation**: Apply fixes and validate
6. **Communication**: Notify affected parties
7. **Post-Mortem**: Document lessons learned

---

## [W] Security Contact

- **Email**: security@flamehaven.io
- **PGP Key**: [Available at https://flamehaven.io/pgp.asc]
- **Response Time**: 48 hours maximum
- **Emergency**: For critical vulnerabilities, include "URGENT" in subject

---

## [+] Hall of Fame

We recognize researchers who responsibly disclose vulnerabilities:

<!-- Contributors will be listed here after responsible disclosure -->

---

## [L] Resources

- **OWASP ML Security**: https://owasp.org/www-project-machine-learning-security/
- **NIST AI Risk Management**: https://www.nist.gov/itl/ai-risk-management-framework
- **Paper**: [`docs/paper.pdf`](docs/paper.pdf) - Security considerations in Section 6

---

**Last Updated**: 2026-01-06  
**Next Review**: 2026-04-06  
**Version**: 1.0.0
