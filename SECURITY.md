# Security policy

## Supported versions

Security fixes are applied to the latest `1.x` release and the current `main`
branch.

## Reporting a vulnerability

Do not open a public issue for a vulnerability, credential exposure, or report
containing private production images.

Use GitHub's private vulnerability reporting flow:

<https://github.com/rezafarjad/industrial-pcb-anomaly-detection/security/advisories/new>

Include:

- the affected version or commit;
- a minimal reproduction;
- the expected impact;
- suggested mitigations, if known.

You should receive an acknowledgement within seven days. Please allow time for
a fix before public disclosure.

## Deployment notes

- The Streamlit app is intended for trusted local or controlled deployments.
- Do not expose it directly to the public internet without authentication,
  request-size limits, TLS termination, and normal reverse-proxy hardening.
- Uploaded images are processed in memory by the running application. Operators
  remain responsible for their image-retention and privacy policies.
