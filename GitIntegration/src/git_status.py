"""
Git Status - Handle git repository status operations
including staging, unstaging, and committing files.
"""

import os
from typing import Dict, List

from git import GitCommandError, InvalidGitRepositoryError, Repo


class GitStatus:
    """Handles git repository status operations"""

    def __init__(self, repo_path: str):
        """
        Initialize GitStatus

        Args:
            repo_path: Path to the git repository
        """
        self.repo_path = repo_path
        try:
            self.repo = Repo(self.repo_path)
        except InvalidGitRepositoryError:
            raise Exception(f"Not a valid git repository: {self.repo_path}")

    def get_status(self) -> Dict:
        """
        Get current git status information

        Returns:
            Dictionary with staged, unstaged, and untracked files
        """
        try:
            # Get staged files
            staged_files = []
            for item in self.repo.index.diff("HEAD"):
                staged_files.append(
                    {
                        "path": item.a_path if item.a_path else item.b_path,
                        "status": (
                            "modified"
                            if item.change_type == "M"
                            else item.change_type.lower()
                        ),
                        "is_staged": True,
                    }
                )

            # Get unstaged files
            unstaged_files = []
            for item in self.repo.index.diff(None):
                unstaged_files.append(
                    {
                        "path": item.a_path if item.a_path else item.b_path,
                        "status": (
                            "modified"
                            if item.change_type == "M"
                            else item.change_type.lower()
                        ),
                        "is_staged": False,
                    }
                )

            # Get untracked files
            untracked_files = []
            for file_path in self.repo.untracked_files:
                untracked_files.append(
                    {
                        "path": file_path,
                        "status": "untracked",
                        "is_staged": False,
                    }
                )

            # Get file contents for diff display
            all_files = staged_files + unstaged_files + untracked_files

            # Add diff information for modified files
            for file_info in all_files:
                file_path = file_info["path"]
                try:
                    if file_info["is_staged"]:
                        # Get diff between HEAD and index for staged files
                        diff = self.repo.git.diff("--cached", "--", file_path)
                        file_info["diff"] = diff
                    elif file_info["status"] != "untracked":
                        # Get diff between working directory and index for unstaged files
                        diff = self.repo.git.diff("--", file_path)
                        file_info["diff"] = diff
                    else:
                        # For untracked files, get the full content
                        full_path = os.path.join(self.repo_path, file_path)
                        if os.path.exists(full_path):
                            with open(
                                full_path, "r", encoding="utf-8", errors="replace"
                            ) as f:
                                file_info["content"] = f.read()
                except Exception:
                    file_info["diff"] = "Error reading file"

            return {
                "staged": staged_files,
                "unstaged": unstaged_files,
                "untracked": untracked_files,
                "branch": self.get_current_branch(),
                "clean": len(all_files) == 0,
            }

        except Exception as e:
            return {
                "staged": [],
                "unstaged": [],
                "untracked": [],
                "branch": "unknown",
                "clean": True,
                "error": str(e),
            }

    def stage_files(self, file_paths: List[str]) -> Dict:
        """
        Stage files for commit

        Args:
            file_paths: List of file paths to stage

        Returns:
            Dictionary with success status and message
        """
        try:
            for file_path in file_paths:
                self.repo.index.add([file_path])

            return {
                "success": True,
                "message": f"Successfully staged {len(file_paths)} file(s)",
            }

        except GitCommandError as e:
            return {"success": False, "message": f"Failed to stage files: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def unstage_files(self, file_paths: List[str]) -> Dict:
        """
        Unstage files from commit

        Args:
            file_paths: List of file paths to unstage

        Returns:
            Dictionary with success status and message
        """
        try:
            # Use git reset command to unstage files
            # This properly handles the file state and keeps it as modified in working directory
            for file_path in file_paths:
                # Use git reset to unstage the file
                self.repo.git.reset("HEAD", "--", file_path)

            return {
                "success": True,
                "message": f"Successfully unstaged {len(file_paths)} file(s)",
            }

        except GitCommandError as e:
            return {"success": False, "message": f"Failed to unstage files: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def commit(self, message: str) -> Dict:
        """
        Commit staged changes

        Args:
            message: Commit message

        Returns:
            Dictionary with success status and message
        """
        try:
            # Check if there are staged changes
            if not self.repo.index.diff("HEAD") and not any(
                self.repo.index.iter_blobs()
            ):
                return {
                    "success": False,
                    "message": "No staged changes to commit",
                }

            # Create commit
            commit = self.repo.index.commit(message)

            return {
                "success": True,
                "message": "Successfully committed changes",
                "commit_sha": commit.hexsha[:8],
                "commit_message": message,
            }

        except GitCommandError as e:
            return {"success": False, "message": f"Failed to commit: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_current_branch(self) -> str:
        """
        Get the name of the current branch

        Returns:
            Current branch name
        """
        try:
            if self.repo.head.is_detached:
                return "HEAD"
            return self.repo.active_branch.name
        except Exception:
            return "unknown"

    def discard_changes(self, file_paths: List[str]) -> Dict:
        """
        Discard changes to files

        Args:
            file_paths: List of file paths to discard changes for

        Returns:
            Dictionary with success status and message
        """
        try:
            for file_path in file_paths:
                # Use git checkout to discard changes
                self.repo.git.checkout("--", file_path)

            return {
                "success": True,
                "message": f"Successfully discarded changes for {len(file_paths)} file(s)",
            }

        except GitCommandError as e:
            return {"success": False, "message": f"Failed to discard changes: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_conflicts(self) -> List[Dict]:
        """
        Get current merge conflicts

        Returns:
            List of conflict dictionaries with file path and conflict markers
        """
        try:
            conflicts = []
            unmerged_blobs = self.repo.index.unmerged_blobs()

            for file_path, blob_entries in unmerged_blobs.items():
                # Read the conflicted file content
                full_path = os.path.join(self.repo_path, file_path)
                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                else:
                    content = ""

                # Parse conflicts
                conflict_sections = self._parse_conflicts(content)

                conflicts.append(
                    {
                        "path": file_path,
                        "content": content,
                        "sections": conflict_sections,
                        "status": self._get_conflict_status(file_path),
                    }
                )

            return conflicts

        except Exception:
            return []

    def _parse_conflicts(self, content: str) -> List[Dict]:
        """
        Parse conflict markers in file content

        Args:
            content: File content with conflict markers

        Returns:
            List of conflict section dictionaries
        """
        sections = []
        lines = content.split("\n")
        i = 0
        conflict_id = 0

        while i < len(lines):
            line = lines[i]

            # Start of conflict
            if line.startswith("<<<<<<<"):
                section = {
                    "id": conflict_id,
                    "start_line": i + 1,
                    "ours": [],
                    "theirs": [],
                    "base": [],
                    "end_line": None,
                }

                # Parse our changes
                i += 1
                while i < len(lines) and not lines[i].startswith("======="):
                    section["ours"].append(lines[i])
                    i += 1

                # Parse their changes
                i += 1  # Skip '======='
                while i < len(lines) and not lines[i].startswith(">>>>>>>"):
                    section["theirs"].append(lines[i])
                    i += 1

                # Find end line
                section["end_line"] = i + 1
                conflict_id += 1

                sections.append(section)

            i += 1

        return sections

    def _get_conflict_status(self, file_path: str) -> str:
        """
        Get conflict status for a file

        Args:
            file_path: Path to the conflicted file

        Returns:
            Conflict status string
        """
        try:
            # Check git status for specific conflict indicators
            status_output = self.repo.git.status("--porcelain").split("\n")
            for line in status_output:
                if file_path in line:
                    # Look for 'UU' which indicates both sides modified
                    if line.startswith("UU "):
                        return "both_modified"
                    # Look for 'AA' which indicates both added
                    elif line.startswith("AA "):
                        return "both_added"
                    # Look for 'DD' which indicates both deleted
                    elif line.startswith("DD "):
                        return "both_deleted"
                    # Look for 'DU' or 'UD' for one deleted, one modified
                    elif line.startswith("DU ") or line.startswith("UD "):
                        return "deleted_modified"
                    break
            return "conflicted"
        except Exception:
            return "conflicted"

    def resolve_conflicts(self, resolutions: List[Dict]) -> Dict:
        """
        Resolve conflicts in files

        Args:
            resolutions: List of resolution dictionaries with file path and chosen sections

        Returns:
            Dictionary with success status and message
        """
        try:
            for resolution in resolutions:
                file_path = resolution.get("path")
                chosen_sections = resolution.get("sections", [])

                if not file_path:
                    continue

                full_path = os.path.join(self.repo_path, file_path)

                # Read current content
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                # Apply resolutions
                resolved_content = self._apply_conflict_resolutions(
                    content, chosen_sections
                )

                # Write resolved content
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(resolved_content)

                # Stage the resolved file
                self.repo.index.add([file_path])

            return {
                "success": True,
                "message": f"Successfully resolved conflicts in {len(resolutions)} file(s)",
            }

        except Exception as e:
            return {"success": False, "message": f"Error resolving conflicts: {str(e)}"}

    def _apply_conflict_resolutions(
        self, content: str, chosen_sections: List[Dict]
    ) -> str:
        """
        Apply conflict resolutions to content

        Args:
            content: Original content with conflict markers
            chosen_sections: List of chosen resolution sections

        Returns:
            Resolved content
        """
        lines = content.split("\n")
        resolved_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this is the start of a conflict
            if line.startswith("<<<<<<<"):
                # Find the resolution for this conflict
                conflict_start = i
                conflict_end = i

                # Find the end of this conflict
                while conflict_end < len(lines) and not lines[conflict_end].startswith(
                    ">>>>>>>"
                ):
                    conflict_end += 1

                # Find which resolution applies
                resolution_applied = False
                for resolution in chosen_sections:
                    if resolution.get("start_line") == conflict_start + 1:
                        # Apply chosen side
                        if resolution.get("choice") == "ours":
                            # Add our changes (between <<<<<<< and =======)
                            j = conflict_start + 1
                            while j < len(lines) and not lines[j].startswith("======="):
                                resolved_lines.append(lines[j])
                                j += 1
                        elif resolution.get("choice") == "theirs":
                            # Add their changes (between ======= and >>>>>>>)
                            j = conflict_start + 1
                            # Skip to the ======= marker
                            while j < len(lines) and not lines[j].startswith("======="):
                                j += 1
                            j += 1  # Skip =======
                            # Add their changes
                            while j < len(lines) and not lines[j].startswith(">>>>>>>"):
                                resolved_lines.append(lines[j])
                                j += 1
                        elif resolution.get("choice") == "manual" and resolution.get(
                            "content"
                        ):
                            # Apply manual resolution
                            manual_lines = resolution["content"].split("\n")
                            resolved_lines.extend(manual_lines)

                        resolution_applied = True
                        break

                if resolution_applied:
                    # Skip the entire conflict section
                    i = conflict_end + 1
                else:
                    # If no resolution found, keep the original conflict
                    resolved_lines.append(line)
                    i += 1
            else:
                # Regular line, just add it
                resolved_lines.append(line)
                i += 1

        return "\n".join(resolved_lines)

    def continue_merge(self) -> Dict:
        """
        Continue merge after resolving conflicts

        Returns:
            Dictionary with success status and message
        """
        try:
            # Check if there are still conflicts
            if self.repo.index.unmerged_blobs():
                return {
                    "success": False,
                    "message": "There are still unresolved conflicts. Please resolve all conflicts before continuing.",
                }

            # Continue merge
            self.repo.git.commit("--no-edit")

            return {
                "success": True,
                "message": "Successfully completed merge",
            }

        except GitCommandError as e:
            return {"success": False, "message": f"Failed to complete merge: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def abort_merge(self) -> Dict:
        """
        Abort current merge operation

        Returns:
            Dictionary with success status and message
        """
        try:
            self.repo.git.merge("--abort")

            return {
                "success": True,
                "message": "Successfully aborted merge",
            }

        except GitCommandError as e:
            return {"success": False, "message": f"Failed to abort merge: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
