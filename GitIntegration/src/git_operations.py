"""
Git Operations - Handle git repository operations
including branch switching, cherry-pick, reset, and merge.
"""

from typing import Dict, List, Optional

from git import GitCommandError, InvalidGitRepositoryError, Repo


class GitOperations:
    """Handles git repository operations"""

    def __init__(self, repo_path: str):
        """
        Initialize GitOperations

        Args:
            repo_path: Path to the git repository
        """
        self.repo_path = repo_path
        try:
            self.repo = Repo(self.repo_path)
        except InvalidGitRepositoryError:
            raise Exception(f"Not a valid git repository: {self.repo_path}")

    def get_branches(self) -> List[Dict]:
        """
        Get all branches in the repository

        Returns:
            List of branch dictionaries with name and is_current properties
        """
        branches = []
        current_branch = None

        try:
            if self.repo.head.is_detached:
                current_branch = "HEAD"
            else:
                current_branch = self.repo.active_branch.name
        except TypeError:
            current_branch = "HEAD"

        # Get local branches
        for branch in self.repo.branches:
            branches.append(
                {
                    "name": branch.name,
                    "is_current": branch.name == current_branch,
                    "type": "local",
                }
            )

        # Get remote branches
        for remote in self.repo.remotes:
            for ref in remote.refs:
                branch_name = f"{remote.name}/{ref.name.split('/')[-1]}"
                branches.append(
                    {"name": branch_name, "is_current": False, "type": "remote"}
                )

        return branches

    def switch_branch(self, branch_name: str) -> Dict:
        """
        Switch to a different branch

        Args:
            branch_name: Name of the branch to switch to

        Returns:
            Dictionary with success status and message
        """
        try:
            # Check if branch exists
            branch = None
            for b in self.repo.branches:
                if b.name == branch_name:
                    branch = b
                    break

            if not branch:
                # Try to find remote branch and create local
                for remote in self.repo.remotes:
                    for ref in remote.refs:
                        if ref.name.split("/")[-1] == branch_name:
                            # Create local branch from remote
                            branch = self.repo.create_head(branch_name, ref)
                            branch.set_tracking_branch(ref)
                            break

            if not branch:
                return {
                    "success": False,
                    "message": f"Branch '{branch_name}' not found",
                }

            # Checkout the branch
            branch.checkout()

            return {
                "success": True,
                "message": f"Successfully switched to branch '{branch_name}'",
                "current_branch": branch_name,
            }

        except GitCommandError as e:
            return {"success": False, "message": f"Failed to switch branch: {str(e)}"}

    def cherry_pick(self, commit_sha: str, target_branch: Optional[str] = None) -> Dict:
        """
        Cherry-pick a commit to a branch

        Args:
            commit_sha: SHA of the commit to cherry-pick
            target_branch: Target branch (None for current branch)

        Returns:
            Dictionary with success status and message
        """
        try:
            # Store current branch if we need to switch
            original_branch = None
            if target_branch and target_branch != self.repo.active_branch.name:
                original_branch = self.repo.active_branch.name
                result = self.switch_branch(target_branch)
                if not result["success"]:
                    return result

            # Perform cherry-pick
            try:
                self.repo.git.cherry_pick(commit_sha)
                message = f"Successfully cherry-picked commit {commit_sha[:8]}"
                if target_branch:
                    message += f" to branch '{target_branch}'"

                result = {"success": True, "message": message}
            except GitCommandError as e:
                # Handle conflicts
                if "CONFLICT" in str(e):
                    result = {
                        "success": False,
                        "message": f"Cherry-pick conflicts detected for commit {commit_sha[:8]}. Please resolve conflicts manually.",
                        "has_conflicts": True,
                    }
                else:
                    result = {
                        "success": False,
                        "message": f"Failed to cherry-pick: {str(e)}",
                    }

            # Switch back to original branch if needed
            if original_branch:
                self.switch_branch(original_branch)

            return result

        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def reset_commits(self, commit_sha: str, mode: str = "mixed") -> Dict:
        """
        Reset branch to a specific commit

        Args:
            commit_sha: SHA of the commit to reset to
            mode: reset mode (soft, mixed, hard)

        Returns:
            Dictionary with success status and message
        """
        try:
            # Validate reset mode
            if mode not in ["soft", "mixed", "hard"]:
                mode = "mixed"

            # Get the commit
            commit = self.repo.commit(commit_sha)

            # Perform reset
            if mode == "soft":
                self.repo.head.reset(commit, index=True, working_tree=False)
            elif mode == "mixed":
                self.repo.head.reset(commit, index=False, working_tree=False)
            elif mode == "hard":
                self.repo.head.reset(commit, index=True, working_tree=True)

            return {
                "success": True,
                "message": f"Successfully performed {mode} reset to commit {commit_sha[:8]}",
            }

        except GitCommandError as e:
            return {"success": False, "message": f"Failed to reset: {str(e)}"}

    def merge_branches(
        self, source_branch: str, target_branch: Optional[str] = None
    ) -> Dict:
        """
        Merge one branch into another

        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into (None for current branch)

        Returns:
            Dictionary with success status and message
        """
        try:
            # Store current branch
            original_branch = self.repo.active_branch.name

            # Switch to target branch if specified
            if target_branch and target_branch != original_branch:
                result = self.switch_branch(target_branch)
                if not result["success"]:
                    return result
                current_branch = target_branch
            else:
                current_branch = original_branch

            # Find source branch
            source = None
            for branch in self.repo.branches:
                if branch.name == source_branch:
                    source = branch
                    break

            if not source:
                # Try remote branches
                for remote in self.repo.remotes:
                    for ref in remote.refs:
                        if ref.name.split("/")[-1] == source_branch:
                            source = ref
                            break

            if not source:
                return {
                    "success": False,
                    "message": f"Branch '{source_branch}' not found",
                }

            # Perform merge
            try:
                merge_result = self.repo.merge(source)
                if merge_result:
                    # Conflicts occurred
                    return {
                        "success": False,
                        "message": "Merge conflicts detected. Please resolve conflicts manually.",
                        "has_conflicts": True,
                        "conflicted_files": list(
                            self.repo.index.unmerged_blobs().keys()
                        ),
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Successfully merged '{source_branch}' into '{current_branch}'",
                    }

            except GitCommandError as e:
                if "CONFLICT" in str(e):
                    return {
                        "success": False,
                        "message": "Merge conflicts detected. Please resolve conflicts manually.",
                        "has_conflicts": True,
                        "conflicted_files": list(
                            self.repo.index.unmerged_blobs().keys()
                        ),
                    }
                else:
                    return {"success": False, "message": f"Failed to merge: {str(e)}"}

        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}

    def get_commit_info(self, commit_sha: str) -> Optional[Dict]:
        """
        Get detailed information about a commit

        Args:
            commit_sha: SHA of the commit

        Returns:
            Dictionary with commit information or None if not found
        """
        try:
            commit = self.repo.commit(commit_sha)
            return {
                "sha": commit.hexsha,
                "short_sha": commit.hexsha[:8],
                "message": commit.message,
                "author": str(commit.author),
                "date": commit.committed_date,
                "parents": [p.hexsha[:8] for p in commit.parents],
                "is_merge": len(commit.parents) > 1,
            }
        except Exception as e:
            # TODO
            print(e)
            return None

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
        except Exception as e:
            # TODO
            print(e)
            return "unknown"
