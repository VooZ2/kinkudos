#!/usr/bin/env python3
"""Build Django-compatible PO and MO files from the reviewed JSON catalog."""

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "locale" / "lt" / "messages.json"
OUTPUT_DIR = ROOT / "locale" / "lt" / "LC_MESSAGES"


def quote(value):
    return json.dumps(value, ensure_ascii=False)


def write_po(messages):
    header = (
        "Project-Id-Version: KinKudos\n"
        "Language: lt\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=UTF-8\n"
        "Content-Transfer-Encoding: 8bit\n"
        "Plural-Forms: nplurals=4; plural=(n%10==1 && (n%100>19 || n%100<11) ? 0 : "
        "(n%10>=2 && n%10<=9) && (n%100>19 || n%100<11) ? 1 : n%1!=0 ? 2: 3);\n"
    )
    lines = ['msgid ""', f"msgstr {quote(header)}", ""]
    for msgid, msgstr in sorted(messages.items()):
        lines.extend((f"msgid {quote(msgid)}", f"msgstr {quote(msgstr)}", ""))
    (OUTPUT_DIR / "django.po").write_text("\n".join(lines), encoding="utf-8")
    return header


def write_mo(messages, header):
    catalog = {"": header, **messages}
    ids = sorted(catalog)
    encoded_ids = [key.encode("utf-8") for key in ids]
    encoded_values = [catalog[key].encode("utf-8") for key in ids]
    count = len(ids)
    key_table_offset = 28
    value_table_offset = key_table_offset + count * 8
    strings_offset = value_table_offset + count * 8

    key_blob = b""
    key_entries = []
    for value in encoded_ids:
        key_entries.append((len(value), strings_offset + len(key_blob)))
        key_blob += value + b"\0"

    value_blob_offset = strings_offset + len(key_blob)
    value_blob = b""
    value_entries = []
    for value in encoded_values:
        value_entries.append((len(value), value_blob_offset + len(value_blob)))
        value_blob += value + b"\0"

    output = struct.pack("<7I", 0x950412DE, 0, count, key_table_offset, value_table_offset, 0, 0)
    output += b"".join(struct.pack("<2I", *entry) for entry in key_entries)
    output += b"".join(struct.pack("<2I", *entry) for entry in value_entries)
    output += key_blob + value_blob
    (OUTPUT_DIR / "django.mo").write_bytes(output)


def main():
    messages = json.loads(CATALOG.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    header = write_po(messages)
    write_mo(messages, header)
    print(f"Compiled {len(messages)} Lithuanian translations.")


if __name__ == "__main__":
    main()
