#!/usr/bin/env python3
import secrets
import argparse
import os

VALID_KEYS_FILE = os.path.join(os.path.dirname(__file__), "valid_keys.txt")

def generate_key(fmt: str = None) -> str:
    """
    Erzeugt einen zufälligen Schlüssel.
    Default: 32 Zeichen, hex (A–F, 0–9).
    Mit fmt z.B. "XXXX-XXXX-XXXX" formatiert.
    """
    raw = secrets.token_hex(16).upper()  # 32 hex‐Zeichen
    if fmt:
        # fmt: "XXXX-XXXX-XXXX" wendet Blocks an
        parts = []
        pos = 0
        for block in fmt.split("-"):
            length = len(block)
            parts.append(raw[pos:pos+length])
            pos += length
        return "-".join(parts)
    return raw

def add_key(key: str):
    """Hängt den neuen Key an valid_keys.txt an (ein Key pro Zeile)."""
    with open(VALID_KEYS_FILE, "a", encoding="utf-8") as f:
        f.write(key + "\n")
    print("✅ Neuer Lizenzschlüssel hinzugefügt:", key)

def list_keys():
    """Zeigt alle gespeicherten Lizenz­schlüssel."""
    if not os.path.exists(VALID_KEYS_FILE):
        print("Keine valid_keys.txt gefunden.")
        return
    with open(VALID_KEYS_FILE, encoding="utf-8") as f:
        for line in f:
            print(line.strip())

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Lizenzschlüssel generieren und verwalten"
    )
    p.add_argument(
        "--new", "-n", action="store_true",
        help="Neuen Lizenzschlüssel erzeugen und speichern"
    )
    p.add_argument(
        "--fmt", "-f", type=str, default=None,
        help="Formatvorlage, z.B. XXXX-XXXX-XXXX"
    )
    p.add_argument(
        "--list", "-l", action="store_true",
        help="Alle gültigen Lizenzschlüssel auflisten"
    )
    args = p.parse_args()

    if args.list:
        list_keys()
    elif args.new:
        key = generate_key(args.fmt)
        add_key(key)
    else:
        p.print_help()
