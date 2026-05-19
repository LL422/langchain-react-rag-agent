"""
Provides unified absolute path resolution for the entire project.
"""
import os


def get_project_root() -> str:
    """
    Get the project root directory.
    """
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    project_root = os.path.dirname(current_dir)
    return project_root


def get_abs_path(relative_path: str) -> str:
    """
    Convert a relative path to an absolute path based on the project root.
    """
    project_root = get_project_root()
    return os.path.join(project_root, relative_path)


if __name__ == '__main__':
    print(get_abs_path("config/config.txt"))
