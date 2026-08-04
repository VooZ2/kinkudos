import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid


def generate_vapid_keys(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    private_path = output_dir / "vapid_private.pem"
    public_path = output_dir / "vapid_public.txt"
    if private_path.exists() or public_path.exists():
        raise FileExistsError("VAPID keys already exist.")

    vapid = Vapid()
    vapid.generate_keys()
    private_path.write_bytes(vapid.private_pem())
    public_raw = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    public_value = base64.urlsafe_b64encode(public_raw).rstrip(b"=")
    public_path.write_bytes(public_value + b"\n")
    os.chmod(private_path, 0o600)
    os.chmod(public_path, 0o600)
    return private_path, public_path
