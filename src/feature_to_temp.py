import os
import shutil

from src.temp_to_feature import removeDuplicates

from .utils.utils import (
    clear_folder,
    map_directory,
    getCodeBlockFromFile,
    getBlockDependencies,
    get_code_block_names,
    getIndividualImports
)

from .utils.split import split_code_into_sections

"""
must copy settings and urls file -- done
add ext packages to imports -- done
fix split blocks issue -- done for now (please investigate to find issue root cause)
convert files to template (zip output folder) -- done 
duplicate code for some files
"""

# ignore_dirs = [".git","media","static"]

# if os.path.exists(project_path) and os.path.isdir(project_path):
#     print(f"Mapping directory: {project_path}\n")
#     map_directory(project_path, ignore_dirs)
# else:
#     print("Invalid directory path.")


def writeCodeToFile(file_path,code,imports):
    # add dependencies import files

    path = file_path.split("/")
    file_name = path.pop()
    file_folder = path.pop()

    dest = f"output/{file_folder}"

    if not os.path.exists(dest):
        os.makedirs(dest)
        print(f"dest '{dest}' created.")
    else:
        print(f"dest '{dest}' already exists.")

    dest = f"{dest}/{file_name}"

    if os.path.exists(dest):
        # append to file
        with open(dest, "r+") as file:
            data = file.read()  # Step 1: Read existing content
        
            file.seek(0)        # Move to the beginning of the file
            file.truncate(0)    # Step 2: Clear the file

            write_data = f"{imports}\n{code}\n{data}"
            chunks = split_code_into_sections(write_data)
            code = []
            imports = []
            
            for chunk in chunks:
                if "import " in chunk:
                    individualImports = getIndividualImports(chunk)
                    imports.extend(individualImports)
                else:
                    code.append(chunk)

            if imports:  # Step 3: Write new content
                imports = removeDuplicates(imports)
                imports = "\n".join(imports)
                file.write(imports + "\n")

            file.write("\n\n")
            code = removeDuplicates(code)
            code = "\n".join(code)
            file.write(code)  # Append old content to new content
    else:
        with open(dest,"w") as file:
            if(len(imports)>0):
                file.write(imports)
                file.write("\n\n")
            file.write(code)

def OneStep(file_path,feature):
    if os.path.exists(file_path):
        with open(file_path,"r") as file:
            data = file.read()
            # print(data.split("\n"))
            # for i in data.split("\n"):
            #     print(i, "  ---  ", i.startswith("\n    "))
            # return
            file_dependencies = split_code_into_sections(data)

            for chunk in file_dependencies:
                if "import " in chunk or "from " in chunk:
                    # print(chunk, " hello")
                    file_dependencies.remove(chunk)
                    file_dependencies.extend(getIndividualImports(chunk))

            # print("dependencies ",file_dependencies)

            # get feature
            feature_code = getCodeBlockFromFile(feature,file_dependencies)

            # get feature dependencies
            feature_dependencies = getBlockDependencies(feature_code,file_dependencies)

            # get feature imports
            deb_imports = [f"from {e['packagePath']} import {e['imports']}" for e in feature_dependencies if e['packagePath'] != "."]

            # write code to output
            writeCodeToFile(file_path,feature_code, "\n".join(deb_imports))

            if len(feature_dependencies) > 0:
                # loop through dependencies
                for feature_dep in feature_dependencies:
                    path,dep = [feature_dep['packagePath'], feature_dep['imports']]
                    
                    if path != ".":
                        if path.startswith("."):
                            new_path = file_path.split("/")
                            new_path.pop()
                            new_path.append(f'{path[1:]}.py')
                            new_path = "/".join(new_path)
                            path = new_path

                        OneStep(path,dep)
                    else:
                        OneStep(file_path,dep)

def getUrlPathForViews(feature,path):
    path_import = ["from django.urls import path"]
    urlpatterns = []

    with open(path,"r") as file:
            data = file.read()
            file_dependencies = split_code_into_sections(data)
            # print(file_dependencies, " hello ", len(file_dependencies))
            chunkImport = [i for i in file_dependencies if "import " in i]
            for importLine in chunkImport:
                if "\n" in importLine or "\n\n" in importLine:
                    lineData = getIndividualImports(importLine)
                    chunkImport.remove(importLine)
                    chunkImport.extend(lineData)
            file_dependencies = [chunk for chunk in file_dependencies if "import " not in chunk]

            # print(chunkImport)
            # for o in chunkImport:
            #     print(o)

            urlPaths = None

            for deb in file_dependencies:
                if get_code_block_names(deb,"urlpatterns"):
                    urlPaths = deb

            if urlPaths != None:
                urlPaths = urlPaths.split("\n")
                if len(urlPaths) > 1:
                    for path in urlPaths:
                        if feature in path:
                            if not path.endswith(","):
                                path += ","

                            urlpatterns.append(path)
                            view = path.split(",")[1].strip()

                            for importLine in chunkImport:
                                imports = importLine.split("import")[1]
                                imports = imports.replace("(","")
                                imports = imports.replace(")","").strip()

                                if "," in imports:
                                    imports = imports.split(",")
                                else:
                                    imports = [imports]

                                for i in imports:
                                    i = i.strip()
                                    if view.startswith(i):
                                        path_import.append(importLine.strip())
    return [urlpatterns, path_import]

# You've not implemented get feature URL
def getURLForFeature(feature,file_path):
    path = file_path.split("/")
    path.pop()  #remove current file in path
    path.append("urls.py") #add urls.py to path
    # print("getting URL for ",feature, " searching ","/".join(path))
    path = "/".join(path)

    # TODO process url differently

    if os.path.exists(path):
        urlpatterns, imports = getUrlPathForViews(feature,path)
        # print("imports is ", imports)
        urlpatterns = "\n".join(urlpatterns)
        urlpatterns = f"urlpatterns = [\n{urlpatterns}\n]"
        imports = "\n".join(imports)

        writeCodeToFile(path,urlpatterns,imports)
    else:
        # get and loop through all url files in the project
        pass


def create_temp_from_feature(project_path,project_name,feature_name,feature_file_path):

    OneStep(feature_file_path,feature_name)
    # if views.py in models, generate url for feature
    getURLForFeature(feature_name,feature_file_path)
    
    # Copy the file
    # TODO: process/edit settings before copying
    source = f"{project_path}/{project_name}/settings.py"
    destination = f"./output/settings.py"
    shutil.copy(source, destination) 

    # Save template
    folder_to_zip = "./output"
    output_zip = f"./speed_build_{feature_name}"  # No .zip extension needed

    shutil.make_archive(output_zip, 'zip', folder_to_zip)

    # delete output folder
    clear_folder(folder_to_zip)