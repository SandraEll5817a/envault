# envault

> Securely sync `.env` files across your team using encrypted S3 or GCS backends.

---

## Installation

```bash
pip install envault
```

Or with optional GCS support:

```bash
pip install envault[gcs]
```

---

## Usage

### Initialize a vault

```bash
envault init --backend s3 --bucket my-team-bucket --region us-east-1
```

### Push your `.env` file

```bash
envault push --env .env --project myapp --stage production
```

### Pull the latest `.env` file

```bash
envault pull --project myapp --stage production
```

envault encrypts your secrets client-side using AES-256 before uploading. Your cloud provider never sees plaintext values.

### Configuration

Set credentials via environment variables or a `~/.envault/config.toml` file:

```toml
[defaults]
backend = "s3"
bucket = "my-team-bucket"
region = "us-east-1"
encryption_key_env = "ENVAULT_SECRET_KEY"
```

---

## Backends

| Backend | Status |
|---------|--------|
| AWS S3 | ✅ Supported |
| Google Cloud Storage | ✅ Supported |
| Azure Blob Storage | 🚧 Coming soon |

---

## Requirements

- Python 3.8+
- AWS or GCP credentials configured in your environment

---

## License

MIT © [envault contributors](LICENSE)