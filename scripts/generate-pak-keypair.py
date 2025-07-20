#!/usr/bin/env python3
"""
Generate RSA key pair for Personal API Keys (PAKs).

This script generates a 2048-bit RSA key pair and saves it to the secrets directory.
The private key is used for signing PAK tokens, and the public key is used for verification.

Usage:
    python scripts/generate-pak-keypair.py [--force]

Options:
    --force    Overwrite existing key files if they exist
"""

import argparse
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_keypair(force: bool = False) -> None:
    """
    Generate RSA key pair and save to secrets directory.

    Args:
        force: Whether to overwrite existing key files
    """
    # Determine secrets directory path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    secrets_dir = project_root / "secrets"

    # Ensure secrets directory exists
    secrets_dir.mkdir(exist_ok=True)

    private_key_file = secrets_dir / "pak_private_key.txt"
    public_key_file = secrets_dir / "pak_public_key.txt"

    # Check if files already exist
    if private_key_file.exists() and not force:
        print(f"Private key file already exists: {private_key_file}")
        print("Use --force to overwrite existing files")
        sys.exit(1)

    if public_key_file.exists() and not force:
        print(f"Public key file already exists: {public_key_file}")
        print("Use --force to overwrite existing files")
        sys.exit(1)

    print("Generating 2048-bit RSA key pair for PAK tokens...")

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Get public key
    public_key = private_key.public_key()

    # Serialize private key to PEM format
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Serialize public key to PEM format
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Write private key to file
    with open(private_key_file, "wb") as f:
        f.write(private_key_pem)

    # Write public key to file
    with open(public_key_file, "wb") as f:
        f.write(public_key_pem)

    # Set secure file permissions (readable only by owner)
    os.chmod(private_key_file, 0o600)
    os.chmod(public_key_file, 0o644)

    print(f"✅ Private key saved to: {private_key_file}")
    print(f"✅ Public key saved to: {public_key_file}")
    print(
        "\n⚠️  IMPORTANT: Keep the private key secure and never commit it to version control!"
    )
    print(
        "The private key is used to sign API tokens and should be treated as a secret."
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate RSA key pair for Personal API Keys (PAKs)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing key files if they exist",
    )

    args = parser.parse_args()

    try:
        generate_keypair(force=args.force)
    except Exception as e:
        print(f"❌ Error generating key pair: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
