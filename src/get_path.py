import os

def get_relative_file_paths(base_dir):
    file_paths = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            # Get the relative path to the base directory
            relative_path = os.path.relpath(os.path.join(root, file), base_dir)
            file_paths.append(relative_path)
    return file_paths

# Example usage
base_directory = "/home/attah/speedbuildTest/ace_app/.sb/speed_build_ManageRecipes"
file_list = get_relative_file_paths(base_directory)
print(file_list)
