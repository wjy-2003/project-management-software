import os
import re

from django.http import JsonResponse
from django.shortcuts import render
from git import Repo


def get_repo_commits(repo_path, max_commits=100):
    """Extract commits from git repository with tree layout information"""
    try:
        repo = Repo(repo_path)
    except Exception as e:
        print(f"Error opening repo: {e}")
        return {"vertices": [], "branches": [], "error": str(e)}

    # Get all commits from current branch
    commits = list(repo.iter_commits(repo.active_branch, max_count=max_commits))

    # Track vertices and branches
    vertices = []
    branches = {}
    # More distinctive colors
    branch_colors = [
        "#e74c3c",
        "#3498db",
        "#2ecc71",
        "#f39c12",
        "#9b59b6",
        "#1abc9c",
        "#e67e22",
        "#34495e",
    ]
    color_index = 0

    # Get actual branch names
    try:
        # Get all branches (both local and remote) and normalize them
        branch_map = {}  # Maps normalized name to the actual reference

        # First, collect all local branches
        for ref in repo.references:
            if ref.name.startswith("refs/heads/"):
                branch_name = re.sub(r"refs/heads/", "", ref.name)
                if branch_name != "HEAD":
                    branch_map[branch_name] = ref.name

        # Then collect remote branches,
        # but only if no local branch with same name exists
        for ref in repo.references:
            if ref.name.startswith("origin/"):
                branch_name = re.sub(r"origin/", "", ref.name)
                if branch_name != "HEAD" and branch_name not in branch_map:
                    branch_map[branch_name] = ref.name

        # Convert to list and sort
        actual_branches = list(branch_map.keys())

        # Ensure current branch is first and valid
        if repo.active_branch:
            current_branch = repo.active_branch.name
        else:
            current_branch = "main"
        if current_branch != "HEAD":
            if current_branch in actual_branches:
                actual_branches.remove(current_branch)
            actual_branches.insert(0, current_branch)
        else:
            actual_branches.insert(0, "main")

        # Fallback to main if somehow empty
        if not actual_branches or actual_branches[0] == "HEAD":
            actual_branches = ["main"]
    except Exception as e:
        print(f"Error getting actual branch names: {e}")
        actual_branches = ["main"]

    # Create vertex objects for each commit
    commit_to_vertex = {}
    vertex_id = 0

    # First pass: create vertices for all commits
    for commit in commits:
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
        vertices.append(vertex)
        commit_to_vertex[commit.hexsha] = vertex
        vertex_id += 1

    # Second pass: establish parent-child relationships
    for i, commit in enumerate(commits):
        vertex = commit_to_vertex[commit.hexsha]

        # Add parent relationships
        for parent in commit.parents:
            if parent.hexsha in commit_to_vertex:
                parent_vertex = commit_to_vertex[parent.hexsha]
                vertex["parents"].append(parent_vertex["id"])
                parent_vertex["children"].append(vertex["id"])

    # Third pass: assign branches and
    # colors using improved layout that respects actual git branches
    processed_commits = set()

    # First, create a mapping of commits to their branches using git references
    commit_to_branches = {}  # Maps commit SHA to list of branch names

    # For each available branch (both local and remote),
    # find which commits belong to it
    for branch_name in actual_branches:
        try:
            # Try to get the branch reference
            branch_ref = None
            for ref in repo.references:
                if ref.name.endswith(branch_name):
                    branch_ref = ref
                    break

            if branch_ref:
                # Get all commits reachable from this branch
                branch_commits = set()
                for commit in repo.iter_commits(branch_ref):
                    branch_commits.add(commit.hexsha)

                # Add this branch to each commit's branch list
                for commit_sha in branch_commits:
                    if commit_sha not in commit_to_branches:
                        commit_to_branches[commit_sha] = []
                    commit_to_branches[commit_sha].append(branch_name)
        except Exception as e:
            print(f"Error accessing branch {branch_name}: {e}")
            continue  # Skip if branch can't be accessed

    # Now assign branches to vertices using the actual branch information
    for vertex in vertices:
        if vertex["id"] in processed_commits:
            continue

        # Try to find the actual branch for this commit
        actual_branches = []
        try:
            # Find the full SHA for this vertex
            for commit in commits:
                if commit.hexsha[:8] == vertex["sha"]:
                    if commit.hexsha in commit_to_branches:
                        actual_branches = commit_to_branches[commit.hexsha]
                    break
        except Exception as e:
            print(f"Error accessing commit {vertex['sha']}: {e}")

        # Choose the best branch for this commit
        chosen_branch = None
        if actual_branches:
            # Prioritize branches we haven't used yet
            for branch in actual_branches:
                if branch not in branches:
                    chosen_branch = branch
                    break
            # If all branches used, pick the first one
            if not chosen_branch:
                chosen_branch = actual_branches[0]
        else:
            # Fallback: use next available branch from actual_branches
            if color_index < len(actual_branches):
                chosen_branch = actual_branches[color_index]
            else:
                chosen_branch = f"branch_{color_index}"
            color_index += 1

        # Get color for the chosen branch
        if chosen_branch not in branches:
            branch_color = branch_colors[len(branches) % len(branch_colors)]
        else:
            branch_color = branches[chosen_branch]["color"]

        # Follow the commit chain for this branch
        current_vertex = vertex
        branch_vertices = []

        while current_vertex and current_vertex["id"] not in processed_commits:
            # Check if this commit should also be on current branch
            try:
                for commit in commits:
                    if commit.hexsha[:8] == current_vertex["sha"]:
                        comit_branches = commit_to_branches.get(commit.hexsha, [])
                        if chosen_branch in comit_branches or not comit_branches:
                            current_vertex["branch"] = chosen_branch
                            current_vertex["color"] = branch_color
                            current_vertex["x"] = len(branches) * 80
                            branch_vertices.append(current_vertex)
                            processed_commits.add(current_vertex["id"])
                        break
            except Exception as e:
                print(f"Error accessing commit {current_vertex['sha']}: {e}")
                current_vertex["branch"] = chosen_branch
                current_vertex["color"] = branch_color
                current_vertex["x"] = len(branches) * 80
                branch_vertices.append(current_vertex)
                processed_commits.add(current_vertex["id"])

            # Move to parent
            if current_vertex["parents"]:
                parent_id = current_vertex["parents"][0]
                current_vertex = next(
                    (v for v in vertices if v["id"] == parent_id), None
                )
            else:
                break

        # Create branch object if we have vertices
        if branch_vertices and chosen_branch not in branches:
            branches[chosen_branch] = {
                "name": chosen_branch,
                "color": branch_color,
                "vertices": [v["id"] for v in branch_vertices],
                "x": len(branches) * 80,
            }

    # Handle special positioning for merge commits
    for vertex in vertices:
        if vertex["is_merge"] and vertex["children"]:
            # Adjust position for better merge visualization
            child_positions = [
                v["x"] for v in vertices if v["id"] in vertex["children"]
            ]
            if child_positions:
                vertex["x"] = sum(child_positions) / len(child_positions)

    return {
        "vertices": vertices,
        "branches": [
            {"name": name, "color": branch["color"], "x": branch["x"]}
            for name, branch in branches.items()
        ],
        "total_commits": len(commits),
    }


def git_graph(request):
    """Render the git graph visualization page"""
    return render(request, "GitIntegration/git_graph.html")


def git_commits_api(request):
    """API endpoint to get commit data as JSON"""
    # Get the repository path - use the current git repository
    repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Get query parameters
    max_commits = int(request.GET.get("max_commits", 100))

    # Extract commit data
    data = get_repo_commits(repo_path, max_commits)

    return JsonResponse(data)
