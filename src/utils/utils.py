import re
import os
import ast
import shutil

def removeDuplicates(code):
    cleaned_code = []
    for line in code:
        if line not in cleaned_code:
            cleaned_code.append(line)

    return cleaned_code


def clear_folder(folder_path):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) or os.path.islink(file_path):  
            os.remove(file_path)  # Delete files & symlinks
        elif os.path.isdir(file_path):  
            shutil.rmtree(file_path)  # Delete directories

def getIndividualImports(code):
    # Split using regex that matches variations of newlines or spaces
    imports = re.split(r'\s*from\s+', code.strip())

    # Filter out empty strings and add 'from' back to the statements
    imports = [f'from {imp.strip()}' for imp in imports if imp.strip()]

    return imports


def get_code_block_names(code,block_name):
    tree = ast.parse(code.strip())
    # print(code," ",block_name)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):  # Function names
            return node.name == block_name
        elif isinstance(node, ast.ClassDef):  # Class names
            return node.name == block_name
        elif isinstance(node, ast.Assign):  # Direct assignments (x = 5, x, y = 10, 20)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == block_name: return True
    return None


def get_assigned_variables(block):
    """Extracts variable names assigned within the given block using AST."""
    assigned_vars = set()
    tree = ast.parse(block.strip())
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):  # Direct assignments (x = 5, x, y = 10, 20)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_vars.add(target.id)
        elif isinstance(node, ast.AnnAssign):  # Type-annotated assignments (x: int = 5)
            if isinstance(node.target, ast.Name):
                assigned_vars.add(node.target.id)
        elif isinstance(node, ast.FunctionDef):  # Function parameters
            for arg in node.args.args:
                assigned_vars.add(arg.arg)
        elif isinstance(node, ast.ClassDef):  # Exclude class names from assigned vars
            assigned_vars.add(node.name)

    return assigned_vars


def getImports(block):
    importLine = []
    for line in block.split("\n"):
        if "import" in line or "from " in line:
            importLine.append(line)

    return importLine


def getBlockDependencies(block, all_blocks):
    importLine = []
    block_words = extract_words_from_code(block)

    # Get assigned variables in the current block
    assigned_vars = get_assigned_variables(block)

    # Remove assigned variables from the dependencies list
    filtered_words = [word for word in block_words if word not in assigned_vars]
    
    filtered_chunks = []
    other_chunks = [] # for class and functions

    # Exclude class and function definitions from all_blocks
    for chunk in all_blocks:
        stripped_chunk = chunk.strip()
        if not (stripped_chunk.startswith("class ") or stripped_chunk.startswith("def ")):
            filtered_chunks.append(chunk)
        else:
            if block != chunk:
                other_chunks.append(chunk)

    all_words = set()

    # Manage imports
    for line in filtered_chunks:
        if "import" in line:
            package_name = line.split("import")[0].split("from")[1].strip()
            if len(package_name) > 0:
                # if package_name not start with .
                # go to our root folder and try and find the file
                # if package_name.startswith(".") or isFileInRoot(package_name) == True:
                char = extract_words_from_code(line.split("import")[1])
                for word in char:
                    if word in filtered_words:
                        all_words.add(word)
                        importLine.append({"packagePath":package_name,"imports":word})
        else:
            # variables line declaration
            varNames = get_assigned_variables(line)
            for word in varNames:
                if word in filtered_words:
                    all_words.add(word)
                    importLine.append({"packagePath":".","imports":word})

    # manage class and functions
    for chunk in other_chunks:
        # print(chunk)
        name = chunk.split("(")[0]
        name = name.replace("def","")
        name = name.replace("class","").strip()
        # print(name)
        if name in filtered_words:
            importLine.append({"packagePath":".","imports":name})

    return importLine

def extract_words_from_code(code):
    # Remove strings and comments
    code = re.sub(r'(".*?"|".*?")', '', code)  # Remove strings
    code = re.sub(r'#.*', '', code)  # Remove comments
    
    # Extract words using regex (identifiers, keywords, function names, variable names)
    words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', code)
    
    return set(words)

def map_directory(directory, ignore_dirs=[], indent=0):
    """
    Recursively traverse a directory and print out its structure, ignoring specified directories.
    """
    try:
        entries = os.listdir(directory)
    except PermissionError:
        print("  " * indent + f"[Access Denied] {directory}")
        return

    for entry in entries:
        path = os.path.join(directory, entry)
        if os.path.isdir(path):
            if entry in ignore_dirs:
                continue
            print("  " * indent + f"[DIR] {entry}")
            map_directory(path, ignore_dirs, indent + 1)
        else:
            print("  " * indent + f"[FILE] {entry}")


def getCodeBlockFromFile(blockName, file_dependencies):
    for chunk in file_dependencies:
        if get_code_block_names(chunk,blockName):
            return chunk
    return None