# Documentation Version History

This file tracks major changes to the documentation set for the **ai-agent-permissions** research prototype.

The documentation provides professional-grade guidance on architecture, security hardening, build processes, configuration, deployment considerations, troubleshooting, compliance gaps, and context for AI coding agents. It is **independent research documentation**, not an official government product.

| Version | Date       | Changes |
|---------|------------|---------|
| 1.0.0   | 2026-05-26 | Initial creation of comprehensive professional documentation set. Includes:<br>• Architecture.md (with Mermaid diagrams)<br>• Security-Hardening.md (control mappings and roadmap)<br>• Build-Process.md, Configuration.md, Deployment.md, Troubleshooting.md<br>• Compliance-Gaps-and-Remediation-Roadmap.md<br>• AI-Agent-Permissions-Context.md (for LLM agents / Grok Build)<br>• SECURITY.md and CONTRIBUTING.md at root |
| 1.0.1   | 2026-05-26 | Reorganization: Moved all non-README `.md` files (SECURITY.md, CONTRIBUTING.md) and `website.pdf` into `docs/`. Updated all cross-references, internal links, and project structure diagrams in README.md and docs/AI-Agent-Permissions-Context.md. |
| 1.0.2   | 2026-05-26 | Removed all classification markings, distribution statements, and official government framing throughout the documentation. Documentation is now clearly positioned as independent research work with no implication of U.S. government, DoD, or Army endorsement or adoption. Updated commit message and all references for consistency. Added this version history file. |

**Notes:**
- All versions maintain a focus on security best practices drawn from public standards (NIST SP 800-53, CNSSI 1253, STIGs, NSA hardening guidance, OWASP LLM Top 10, etc.).
- No source code or research data (in `data/`) was modified during documentation work.
- Future changes to the documentation should be recorded in this table.