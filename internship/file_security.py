from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

from django.core.exceptions import ValidationError


@dataclass(frozen=True)
class FileRule:
    label: str
    extensions: tuple[str, ...]
    mime_types: tuple[str, ...]
    max_size: int
    required_signature: bytes | None = None

    @property
    def max_size_mb(self) -> int:
        return max(1, round(self.max_size / (1024 * 1024)))


GENERIC_MIME_TYPES = ("application/octet-stream", "binary/octet-stream")

PDF_RULE = FileRule(
    label="PDF",
    extensions=(".pdf",),
    mime_types=("application/pdf", "application/x-pdf", *GENERIC_MIME_TYPES),
    max_size=5 * 1024 * 1024,
    required_signature=b"%PDF",
)

CHAT_IMAGE_RULE = FileRule(
    label="görsel",
    extensions=(".png", ".jpg", ".jpeg", ".webp"),
    mime_types=("image/png", "image/jpeg", "image/webp", *GENERIC_MIME_TYPES),
    max_size=4 * 1024 * 1024,
)

CHAT_WORD_RULE = FileRule(
    label="Word belgesi",
    extensions=(".doc", ".docx"),
    mime_types=(
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        *GENERIC_MIME_TYPES,
    ),
    max_size=6 * 1024 * 1024,
)

DOCUMENT_RULES: dict[str, FileRule] = {
    "intern_agreement": FileRule(
        label="staj sözleşmesi",
        extensions=(".pdf",),
        mime_types=PDF_RULE.mime_types,
        max_size=5 * 1024 * 1024,
        required_signature=b"%PDF",
    ),
    "daily_form": FileRule(
        label="imzalı günlük formu",
        extensions=(".pdf",),
        mime_types=PDF_RULE.mime_types,
        max_size=6 * 1024 * 1024,
        required_signature=b"%PDF",
    ),
    "report": FileRule(
        label="staj raporu",
        extensions=(".pdf",),
        mime_types=PDF_RULE.mime_types,
        max_size=10 * 1024 * 1024,
        required_signature=b"%PDF",
    ),
    "presentation": FileRule(
        label="sunum dosyası",
        extensions=(".pdf", ".ppt", ".pptx"),
        mime_types=(
            "application/pdf",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            *GENERIC_MIME_TYPES,
        ),
        max_size=12 * 1024 * 1024,
        required_signature=None,
    ),
}


def _normalize_extension(file_name: str) -> str:
    return os.path.splitext((file_name or "").lower())[1]


def _read_prefix(uploaded_file, size: int) -> bytes:
    prefix = uploaded_file.read(size)
    uploaded_file.seek(0)
    return prefix


def validate_uploaded_file(uploaded_file, rule: FileRule) -> None:
    if not uploaded_file:
        return

    extension = _normalize_extension(getattr(uploaded_file, "name", ""))
    if extension not in rule.extensions:
        raise ValidationError(
            f"{rule.label.capitalize()} için izin verilen uzantılar: {', '.join(rule.extensions)}."
        )

    if getattr(uploaded_file, "size", 0) > rule.max_size:
        raise ValidationError(f"{rule.label.capitalize()} dosyası en fazla {rule.max_size_mb} MB olabilir.")

    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type and content_type not in rule.mime_types:
        raise ValidationError(f"Yüklenen dosya beklenen {rule.label} formatına uymuyor.")

    if rule.required_signature:
        prefix = _read_prefix(uploaded_file, len(rule.required_signature))
        if prefix != rule.required_signature:
            raise ValidationError(f"Yüklenen dosya geçerli bir {rule.label} dosyası değil.")


def allowed_accept_value(rule: FileRule | Iterable[FileRule]) -> str:
    if isinstance(rule, FileRule):
        return ",".join(rule.extensions)
    extensions: list[str] = []
    for item in rule:
        extensions.extend(item.extensions)
    return ",".join(dict.fromkeys(extensions))
