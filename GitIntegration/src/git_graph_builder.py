"""
Git Graph Builder - Handles the construction of git commit graph data
 including node positioning and branch assignment.
"""

import logging
import re
from typing import Dict, List, Set

from git import Repo

logger = logging.getLogger(__name__)


class GitGraphBuilder:
    """Builds graph data structure for git visualization"""

    # Default branch colors for visualization
    BRANCH_COLORS = [
        "#e74c3c",
        "#3498db",
        "#2ecc71",
        "#f39c12",
        "#9b59b6",
        "#1abc9c",
        "#e67e22",
        "#34495e",
    ]

    def __init__(self, repo_path: str, max_commits: int = 100):
        """
        Initialize the graph builder

        Args:
            repo_path: Path to the git repository
            max_commits: Maximum number of commits to process
        """
        self.repo_path = repo_path
        self.max_commits = max_commits
        self.repo = None
        self.commits = []
        self.vertices = []
        self.branches = {}

    def build_graph(self) -> Dict:
        """
        Build the complete graph structure

        Returns:
            Dictionary containing vertices, branches, and metadata
        """
        try:
            self._load_repository()
            self._create_vertices()
            self._establish_relationships()
            self._assign_branches()
            self._optimize_merge_positions()

            return {
                "vertices": self.vertices,
                "branches": self._get_branch_data(),
                "total_commits": len(self.commits),
                "active_branch_name": (
                    self.repo.active_branch.name if self.repo.active_branch else "main"
                ),
            }
        except Exception as e:
            logger.error(
                f"Error building git graph for repository '{self.repo_path}': {str(e)}"
            )
            return {"vertices": [], "branches": [], "error": str(e)}

    def _load_repository(self) -> None:
        """Load the git repository and commits"""
        try:
            self.repo = Repo(self.repo_path)
            self.commits = list(
                self.repo.iter_commits(
                    self.repo.active_branch, max_count=self.max_commits
                )
            )
        except Exception as e:
            raise Exception(f"Failed to load repository: {e}")

    def _get_actual_branches(self) -> List[str]:
        """
        Get list of actual branch names from repository

        Returns:
            List of branch names with active branch first
        """
        branch_map = {}

        # Collect local branches
        for ref in self.repo.references:
            if ref.name.startswith("refs/heads/"):
                branch_name = re.sub(r"refs/heads/", "", ref.name)
                if branch_name != "HEAD":
                    branch_map[branch_name] = ref.name

        # Collect remote branches (if no local branch with same name)
        for ref in self.repo.references:
            if ref.name.startswith("origin/"):
                branch_name = re.sub(r"origin/", "", ref.name)
                if branch_name != "HEAD" and branch_name not in branch_map:
                    branch_map[branch_name] = ref.name

        actual_branches = list(branch_map.keys())

        # Ensure active branch is first
        if self.repo.active_branch:
            current_branch = self.repo.active_branch.name
        else:
            current_branch = "main"

        if current_branch != "HEAD":
            if current_branch in actual_branches:
                actual_branches.remove(current_branch)
            actual_branches.insert(0, current_branch)
        else:
            actual_branches.insert(0, "main")

        # Fallback
        if not actual_branches or actual_branches[0] == "HEAD":
            actual_branches = ["main"]

        return actual_branches

    def _create_vertices(self) -> None:
        """Create vertex objects for each commit"""
        self.vertices = []
        commit_to_vertex = {}

        for vertex_id, commit in enumerate(self.commits):
            vertex = {
                "id": vertex_id,
                "sha": commit.hexsha[:8],
                "message": commit.message.split("\n")[0],
                "author": commit.author.name,
                "date": commit.committed_date,
                "parents": [],
                "children": [],
                "branch": None,
                "color": None,
                "x": 0,
                "y": vertex_id * 60,  # Vertical spacing
                "is_merge": len(commit.parents) > 1,
            }
            self.vertices.append(vertex)
            commit_to_vertex[commit.hexsha] = vertex

    def _establish_relationships(self) -> None:
        """Establish parent-child relationships between vertices"""
        # Create mapping from SHA to vertex
        commit_to_vertex = {}
        for vertex in self.vertices:
            # Find full SHA for this vertex
            for commit in self.commits:
                if commit.hexsha[:8] == vertex["sha"]:
                    commit_to_vertex[commit.hexsha] = vertex
                    break

        # Establish relationships
        for commit in self.commits:
            if commit.hexsha in commit_to_vertex:
                vertex = commit_to_vertex[commit.hexsha]
                for parent in commit.parents:
                    if parent.hexsha in commit_to_vertex:
                        parent_vertex = commit_to_vertex[parent.hexsha]
                        vertex["parents"].append(parent_vertex["id"])
                        parent_vertex["children"].append(vertex["id"])

    def _build_commit_to_branches_map(
        self, actual_branches: List[str]
    ) -> Dict[str, List[str]]:
        """
        Build mapping of commits to their branches

        Args:
            actual_branches: List of branch names

        Returns:
            Dictionary mapping commit SHA to list of branch names
        """
        commit_to_branches = {}

        for branch_name in actual_branches:
            try:
                # Get branch reference
                branch_ref = None
                for ref in self.repo.references:
                    if ref.name.endswith(branch_name):
                        branch_ref = ref
                        break

                if branch_ref:
                    # Get all commits reachable from this branch
                    branch_commits = set()
                    for commit in self.repo.iter_commits(branch_ref):
                        branch_commits.add(commit.hexsha)

                    # Add branch to each commit's branch list
                    for commit_sha in branch_commits:
                        if commit_sha not in commit_to_branches:
                            commit_to_branches[commit_sha] = []
                        commit_to_branches[commit_sha].append(branch_name)
            except Exception as e:
                logger.warning(
                    f"Error accessing branch '{branch_name}' in repository '{self.repo_path}': {str(e)}"
                )
                continue

        return commit_to_branches

    def _assign_branches(self) -> None:
        """Assign branches and colors to vertices"""
        actual_branches = self._get_actual_branches()
        commit_to_branches = self._build_commit_to_branches_map(actual_branches)
        processed_commits = set()
        color_index = 0

        # Build SHA to vertex mapping
        sha_to_vertex = {}
        for vertex in self.vertices:
            for commit in self.commits:
                if commit.hexsha[:8] == vertex["sha"]:
                    sha_to_vertex[commit.hexsha] = vertex
                    break

        for vertex in self.vertices:
            if vertex["id"] in processed_commits:
                continue

            # Find branches for this commit
            commit_branches = []
            for commit in self.commits:
                if commit.hexsha[:8] == vertex["sha"]:
                    commit_branches = commit_to_branches.get(commit.hexsha, [])
                    break

            # Choose best branch
            chosen_branch = self._choose_branch(
                commit_branches, actual_branches, color_index
            )
            if chosen_branch.startswith("branch_"):
                color_index += 1

            # Get branch color
            branch_color = self._get_branch_color(chosen_branch)

            # Assign branch to commit chain
            self._assign_branch_to_chain(
                vertex,
                chosen_branch,
                branch_color,
                processed_commits,
                commit_to_branches,
            )

    def _choose_branch(
        self, commit_branches: List[str], actual_branches: List[str], color_index: int
    ) -> str:
        """
        Choose the best branch for a commit

        Args:
            commit_branches: List of branches containing this commit
            actual_branches: List of all available branches
            color_index: Current color index

        Returns:
            Chosen branch name
        """
        if commit_branches:
            # Prioritize unused branches
            for branch in commit_branches:
                if branch not in self.branches:
                    return branch
            # If all used, pick first
            return commit_branches[0]
        else:
            # Fallback to next available branch
            if color_index < len(actual_branches):
                return actual_branches[color_index]
            else:
                return f"branch_{color_index}"

    def _get_branch_color(self, branch_name: str) -> str:
        """
        Get color for a branch

        Args:
            branch_name: Name of the branch

        Returns:
            Hex color code
        """
        if branch_name not in self.branches:
            return self.BRANCH_COLORS[len(self.branches) % len(self.BRANCH_COLORS)]
        return self.branches[branch_name]["color"]

    def _assign_branch_to_chain(
        self,
        start_vertex: Dict,
        chosen_branch: str,
        branch_color: str,
        processed_commits: Set[int],
        commit_to_branches: Dict[str, List[str]],
    ) -> None:
        """
        Assign branch to a chain of commits

        Args:
            start_vertex: Starting vertex
            chosen_branch: Branch name to assign
            branch_color: Color for the branch
            processed_commits: Set of already processed commit IDs
            commit_to_branches: Mapping of commits to branches
        """
        current_vertex = start_vertex
        branch_vertices = []

        # Build SHA to vertex mapping for lookup
        sha_to_vertex = {}
        for vertex in self.vertices:
            for commit in self.commits:
                if commit.hexsha[:8] == vertex["sha"]:
                    sha_to_vertex[commit.hexsha] = vertex
                    break

        while current_vertex and current_vertex["id"] not in processed_commits:
            # Check if commit belongs to chosen branch
            should_assign = True
            for commit in self.commits:
                if commit.hexsha[:8] == current_vertex["sha"]:
                    commit_branches = commit_to_branches.get(commit.hexsha, [])
                    if chosen_branch not in commit_branches and commit_branches:
                        should_assign = False
                    break

            if should_assign:
                current_vertex["branch"] = chosen_branch
                current_vertex["color"] = branch_color
                current_vertex["x"] = len(self.branches) * 80
                branch_vertices.append(current_vertex)
                processed_commits.add(current_vertex["id"])

            # Move to parent
            if current_vertex["parents"]:
                parent_id = current_vertex["parents"][0]
                current_vertex = next(
                    (v for v in self.vertices if v["id"] == parent_id), None
                )
            else:
                break

        # Create branch object
        if branch_vertices and chosen_branch not in self.branches:
            self.branches[chosen_branch] = {
                "name": chosen_branch,
                "color": branch_color,
                "vertices": [v["id"] for v in branch_vertices],
                "x": len(self.branches) * 80,
            }

    def _optimize_merge_positions(self) -> None:
        """Optimize positions of merge commits for better visualization"""
        for vertex in self.vertices:
            if vertex["is_merge"] and vertex["children"]:
                # Position merge commits at average of children's positions
                child_positions = [
                    v["x"] for v in self.vertices if v["id"] in vertex["children"]
                ]
                if child_positions:
                    vertex["x"] = sum(child_positions) / len(child_positions)

    def _get_branch_data(self) -> List[Dict]:
        """
        Get branch data for output

        Returns:
            List of branch dictionaries
        """
        return [
            {"name": name, "color": branch["color"], "x": branch["x"]}
            for name, branch in self.branches.items()
        ]


def get_repo_commits(repo_path: str, max_commits: int = 100) -> Dict:
    """
    Convenience function to build git graph data

    Args:
        repo_path: Path to the git repository
        max_commits: Maximum number of commits to process

    Returns:
        Dictionary containing graph data
    """
    builder = GitGraphBuilder(repo_path, max_commits)
    return builder.build_graph()
