"""
Load TLS inspection firewall certificate and configure Python SSL trust.

For Lambda functions: Call init_firewall_cert() at module level (before any HTTPS calls).
For Docker containers: Use the load_firewall_cert.py script in startup instead.

Only active when IS_PRIVATE_DEPLOY=true.
"""

import json
import os
import ssl
from pathlib import Path

CERT_SECRET_NAME = "/network-firewall/ca-certificate"
COMBINED_BUNDLE_PATH = "/tmp/combined-ca-bundle.crt"


def init_firewall_cert() -> None:
    """
    Initialize firewall certificate trust for Lambda environments.

    Fetches the certificate from Secrets Manager, combines it with the system CA bundle,
    and configures environment variables so all HTTP clients trust it.

    Should be called at module level before any HTTPS calls are made.
    """
    is_private_deploy = os.environ.get("IS_PRIVATE_DEPLOY", "").lower() == "true"

    if not is_private_deploy:
        return

    if Path(COMBINED_BUNDLE_PATH).exists():
        # Already initialized (warm start)
        return

    import boto3
    from botocore.exceptions import ClientError

    try:
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager")
        response = client.get_secret_value(SecretId=CERT_SECRET_NAME)
        secret_data = json.loads(response["SecretString"])
        firewall_cert = secret_data["certificate"]
    except ClientError as e:
        raise RuntimeError(f"Failed to fetch firewall certificate: {e}") from e

    # Get the default CA bundle (certifi or system)
    default_ca_bundle = ssl.get_default_verify_paths().cafile
    if default_ca_bundle and Path(default_ca_bundle).exists():
        system_certs = Path(default_ca_bundle).read_text()
    else:
        # Fallback to certifi if available
        try:
            import certifi

            system_certs = Path(certifi.where()).read_text()
        except ImportError:
            system_certs = ""

    # Combine system certs with firewall cert
    combined = system_certs
    if not combined.endswith("\n"):
        combined += "\n"
    combined += firewall_cert
    if not combined.endswith("\n"):
        combined += "\n"

    Path(COMBINED_BUNDLE_PATH).write_text(combined)

    # Set environment variables for all HTTP clients
    os.environ["SSL_CERT_FILE"] = COMBINED_BUNDLE_PATH
    os.environ["REQUESTS_CA_BUNDLE"] = COMBINED_BUNDLE_PATH
    os.environ["AWS_CA_BUNDLE"] = COMBINED_BUNDLE_PATH
    os.environ["CURL_CA_BUNDLE"] = COMBINED_BUNDLE_PATH
