class DomainError(Exception):
    """Base class for application-level domain errors."""


class OCRProcessingError(DomainError):
    """Raised when OCR/document text extraction fails."""


class LLMParseError(DomainError):
    """Raised when LLM response cannot be parsed/validated."""


class ValidationError(DomainError):
    """Raised when extracted invoice data violates business rules."""


class PersistenceError(DomainError):
    """Raised when database persistence fails."""
