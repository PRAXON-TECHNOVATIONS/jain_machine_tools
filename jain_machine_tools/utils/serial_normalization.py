from __future__ import annotations


def normalize_serial_no(value: str | None) -> str:
	if not value:
		return ""

	return value.strip().upper()


def normalize_serial_no_list(value: str | None) -> list[str]:
	if not value:
		return []

	return [normalized for row in value.splitlines() if (normalized := normalize_serial_no(row))]


def normalize_serial_no_multiline(value: str | None) -> str:
	return "\n".join(normalize_serial_no_list(value))
