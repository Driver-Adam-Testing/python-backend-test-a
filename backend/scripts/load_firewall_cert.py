#!/usr/bin/env python3
"""
Load TLS inspection firewall certificate from AWS Secrets Manager and add it to the system trust store.

This script runs early in container startup (before prestart.sh) to ensure the firewall's
CA certificate is trusted before any outbound HTTPS connections are made.

Only runs when IS_PRIVATE_DEPLOY=true.
"""

import json
import os
import subprocess
import sys

CERT_SECRET_NAME = "/network-firewall/ca-certificate"
CERT_OUTPUT_PATH = "/usr/local/share/ca-certificates/network-firewall.crt"


def load_firewall_certificate() -> None:
    is_private_deploy = os.environ.get("IS_PRIVATE_DEPLOY", "").lower() == "true"

    if not is_private_deploy:
        print("IS_PRIVATE_DEPLOY is not true, skipping firewall certificate loading")
        return

    print(f"Loading firewall certificate from Secrets Manager: {CERT_SECRET_NAME}")

    import boto3
    from botocore.exceptions import ClientError

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    response = client.get_secret_value(SecretId=CERT_SECRET_NAME)
    secret_data = json.loads(response["SecretString"])
    certificate = secret_data["certificate"]

    print(f"Writing certificate to {CERT_OUTPUT_PATH}")
    with open(CERT_OUTPUT_PATH, "w") as f:
        f.write(certificate)
        if not certificate.endswith("\n"):
            f.write("\n")

    print("Updating system CA certificates")
    result = subprocess.run(
        ["update-ca-certificates"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"update-ca-certificates failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"Certificate loaded successfully: {result.stdout.strip()}")


if __name__ == "__main__":
    try:
        load_firewall_certificate()
    except Exception as e:
        print(f"Failed to load firewall certificate: {e}", file=sys.stderr)
        sys.exit(1)
