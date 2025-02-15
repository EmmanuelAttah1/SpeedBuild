import ast
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class CodeSection:
    """Represents a section of code with its type and content."""
    type: str
    content: str
    name: Optional[str] = None
    line_number: int = 0

class PythonCodeSplitter:
    """A class to split Python code into logical sections."""
    
    def __init__(self, code: str):
        self.code = code
        self.lines = code.split('\n')
        self.sections: List[CodeSection] = []
        self.processed_lines = set()  # Track which lines have been processed

    def parse(self) -> List[CodeSection]:
        """Parse the code and split it into sections."""
        try:
            tree = ast.parse(self.code)
            
            # First pass: collect all nodes
            nodes = list(ast.iter_child_nodes(tree))
            
            # Process imports first (grouping consecutive imports)
            i = 0
            while i < len(nodes):
                if isinstance(nodes[i], (ast.Import, ast.ImportFrom)):
                    # Find consecutive imports
                    start_line = nodes[i].lineno - 1
                    end_line = start_line + 1
                    j = i + 1
                    while j < len(nodes) and isinstance(nodes[j], (ast.Import, ast.ImportFrom)):
                        end_line = nodes[j].lineno
                        j += 1
                    i = j  # Skip the processed imports
                    
                    # Create import section
                    content = '\n'.join(self.lines[start_line:end_line])
                    if content.strip():  # Ensure content isn't empty
                        self.sections.append(CodeSection('import', content, line_number=start_line))
                        # Mark these lines as processed
                        for line_num in range(start_line, end_line):
                            self.processed_lines.add(line_num)
                else:
                    # Process non-import nodes
                    section = self._process_node(nodes[i])
                    if section:
                        # Check if any of these lines have been processed
                        start_line = nodes[i].lineno - 1
                        end_line = (nodes[i].end_lineno if hasattr(nodes[i], 'end_lineno') else start_line) + 1
                        
                        # Only add if none of these lines have been processed
                        if not any(line_num in self.processed_lines 
                                 for line_num in range(start_line, end_line)):
                            self.sections.append(section)
                            # Mark these lines as processed
                            for line_num in range(start_line, end_line):
                                self.processed_lines.add(line_num)
                    i += 1
            
            # Sort sections by line number
            self.sections.sort(key=lambda x: x.line_number)
            return self.sections
            
        except SyntaxError as e:
            print(f"Syntax error in code: {e}")
            return self.sections

    def _process_node(self, node: ast.AST) -> Optional[CodeSection]:
        """Process an AST node and return appropriate CodeSection."""
        if not hasattr(node, 'lineno'):
            return None

        start_line = node.lineno - 1
        end_line = (node.end_lineno if hasattr(node, 'end_lineno') else start_line) + 1
        content = '\n'.join(self.lines[start_line:end_line])
        
        if isinstance(node, ast.Assign):
            # Only consider module-level variables
            if isinstance(node.targets[0], ast.Name):
                return CodeSection('variable', content, 
                                name=node.targets[0].id,
                                line_number=start_line)
                
        elif isinstance(node, ast.FunctionDef):
            return CodeSection('function', content,
                            name=node.name,
                            line_number=start_line)
            
        elif isinstance(node, ast.ClassDef):
            return CodeSection('class', content,
                            name=node.name,
                            line_number=start_line)
            
        return None

def split_code_into_sections(code: str) -> List[str]:
    """
    Split Python code into chunks.
    
    Args:
        code (str): The Python source code to split
        
    Returns:
        List[str]: List of code chunks
    """
    splitter = PythonCodeSplitter(code)
    sections = splitter.parse()
    return [section.content for section in sections]

# # Example usage
# if __name__ == "__main__":
#     with open("/home/attah/jannis/jannis_health/jannis_resource/models.py","r") as file:
#         data = file.read()
#         chunks = split_code_into_sections(data)
#         for chunk in chunks:
#             print("\n---")
#             print(chunk.strip())
#         # print(chunks,"  ", len(chunks))
#     sample_code = """
# import math
# from typing import List

# PI = 3.14159
# DEBUG = True

# def calculate_area(radius: float) -> float:
#     return PI * radius * radius

# class Circle:
#     def __init__(self, radius):
#         self.radius = radius
        
#     def area(self):
#         return calculate_area(self.radius)

# result = calculate_area(5)
# """
    
#     # chunks = split_code_into_sections(sample_code)
#     # print("Code chunks:")
#     # for chunk in chunks:
#     #     print("\n---")
#     #     print(chunk.strip())