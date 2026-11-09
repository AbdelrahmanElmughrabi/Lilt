"""Bounds at the file, parser and native API entry points."""
MAX_MARKDOWN_BYTES = 2 * 1024 * 1024
MAX_FILE_BATCH = 32


def markdown_text(value):
    if not isinstance(value, str):
        raise ValueError('The document must contain text.')
    if len(value) > MAX_MARKDOWN_BYTES or len(value.encode('utf-8')) > MAX_MARKDOWN_BYTES:
        raise ValueError('A reading can contain up to 2 MB of Markdown. Split this text into smaller readings.')
    return value
