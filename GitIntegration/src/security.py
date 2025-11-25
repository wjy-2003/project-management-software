"""
Security utilities for Git integration to prevent path traversal attacks
and validate git repository access.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Union

from django.conf import settings

logger = logging.getLogger(__name__)


class GitPathValidationError(Exception):
    """Exception raised when git path validation fails."""

    pass


def validate_git_repository_path(path: Union[str, Path]) -> Path:
    """
    Validate that a given path is safe and within allowed boundaries.

    Args:
        path: The path to validate

    Returns:
        Path: The validated and normalized path

    Raises:
        GitPathValidationError: If path is invalid or outside allowed boundaries
    """
    if not path:
        raise GitPathValidationError("Path cannot be empty")

    # Convert to Path object and normalize
    try:
        normalized_path = Path(path).resolve()
    except (OSError, ValueError) as e:
        raise GitPathValidationError(f"Invalid path: {e}")

    # Check if path exists
    if not normalized_path.exists():
        raise GitPathValidationError(f"Path does not exist: {normalized_path}")

    # Check if it's a directory
    if not normalized_path.is_dir():
        raise GitPathValidationError(f"Path is not a directory: {normalized_path}")

    # Check if it's a git repository
    if not is_git_repository(normalized_path):
        raise GitPathValidationError(f"Not a git repository: {normalized_path}")

    # Check if path is within allowed boundaries
    if not is_path_allowed(normalized_path):
        raise GitPathValidationError(
            f"Path is outside allowed boundaries: {normalized_path}. "
            f"Allowed bases: {settings.ALLOWED_GIT_REPOSITORY_BASES}"
        )

    logger.info(f"Validated git repository path: {normalized_path}")
    return normalized_path


def is_git_repository(path: Path) -> bool:
    """
    Check if a directory is a git repository.

    Args:
        path: Directory path to check

    Returns:
        bool: True if it's a git repository, False otherwise
    """
    # Check for .git directory
    git_dir = path / ".git"
    if git_dir.is_dir():
        # Check for required git files
        required_files = ["HEAD", "config", "refs"]
        return all((git_dir / f).exists() for f in required_files)

    # Check for .git file (git worktree or separate git directory)
    git_file = path / ".git"
    if git_file.is_file():
        try:
            with open(git_file, "r") as f:
                content = f.read().strip()
                # Should contain something like: gitdir: /path/to/.git
                return content.startswith("gitdir:")
        except (OSError, IOError):
            return False

    return False


def is_path_allowed(path: Path) -> bool:
    """
    Check if a path is within the allowed base directories.

    Args:
        path: Path to check

    Returns:
        bool: True if path is allowed, False otherwise
    """
    try:
        normalized_path = path.resolve()
    except (OSError, ValueError):
        return False

    # Check against each allowed base directory
    for base_dir in settings.ALLOWED_GIT_REPOSITORY_BASES:
        try:
            base = Path(base_dir).resolve()
            # Use commonpath to check if normalized_path is under base
            try:
                common = Path(os.path.commonpath([str(normalized_path), str(base)]))
                if common == base:
                    return True
            except ValueError:
                # Paths have no common path (different drives on Windows, etc.)
                continue
        except (OSError, ValueError):
            continue

    return False


def get_allowed_base_directories() -> List[str]:
    """
    Get the list of allowed base directories as strings.

    Returns:
        List[str]: List of allowed base directory paths
    """
    return [
        str(Path(base_dir).resolve())
        for base_dir in settings.ALLOWED_GIT_REPOSITORY_BASES
    ]


def sanitize_path_string(path_string: str) -> str:
    """
    Sanitize a path string to prevent obvious attacks.

    Args:
        path_string: Raw path string

    Returns:
        str: Sanitized path string
    """
    if not path_string:
        return ""

    # Remove dangerous characters
    dangerous_chars = ["<", ">", "|", ";", "&", "`", "$", '"', "'"]
    sanitized = path_string
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    # Limit length
    if len(sanitized) > 1000:  # Arbitrary reasonable limit
        raise GitPathValidationError("Path string too long")

    return sanitized.strip()


def get_default_git_repository_path() -> Path:
    """
    Get the default git repository path from settings.

    Returns:
        Path: The default git repository path
    """
    default_path = settings.DEFAULT_GIT_REPOSITORY_PATH

    # Ensure it's a git repository, otherwise fall back to project root
    if not is_git_repository(default_path):
        logger.warning(
            f"Default git repository path is not a git repository: {default_path}. "
            f"Falling back to project root."
        )
        default_path = Path(settings.BASE_DIR)

    return default_path.resolve()


def log_git_operation(
    operation: str, path: Path, user: Optional[str] = None, success: bool = True
) -> None:
    """
    Log git operations for security monitoring.

    Args:
        operation: The git operation being performed
        path: The repository path
        user: The user performing the operation (if available)
        success: Whether the operation was successful
    """
    if not settings.GIT_OPERATION_LOGGING:
        return

    log_level = logging.INFO if success else logging.WARNING
    message = f"Git operation '{operation}' on path '{path}'"
    if user:
        message += f" by user '{user}'"
    message += f" - {'SUCCESS' if success else 'FAILED'}"

    logger.log(log_level, message)
