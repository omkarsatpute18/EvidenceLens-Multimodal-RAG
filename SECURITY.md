# Security

EvidenceLens treats uploaded content as untrusted data, not instructions. Do not upload credentials or personal data to a demo deployment. Configure API keys through environment variables only. The MVP sanitizes filenames, enforces upload-size and extension limits, avoids logging payloads, and returns uncertainty when visual extraction is ambiguous.

For a production deployment, add authentication, encrypted storage, malware scanning, rate limiting, and isolated per-user evidence stores before accepting sensitive material.
