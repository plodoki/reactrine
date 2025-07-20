#!/usr/bin/env python3
import os
import sys

import httpx


def main():
    token = os.getenv("PAK_TOKEN")
    if not token:
        print(
            "Error: Please set the PAK_TOKEN environment variable to your API key JWT."
        )
        print("Example: export PAK_TOKEN=eyJhbGciOi...\n")
        sys.exit(1)

    base_url = os.getenv("BASE_URL", "http://localhost:3000")
    url = f"{base_url}/api/v1/auth/me"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = httpx.get(url, headers=headers)
    except Exception as e:
        print(f"Request failed: {e}")
        sys.exit(1)

    print(f"Status code: {response.status_code}")
    try:
        data = response.json()
        print("Response JSON:", data)
    except ValueError:
        print("Response text:", response.text)


if __name__ == "__main__":
    main()
