import os, zipfile, sys
from .utils.utils import getIndividualImports,removeDuplicates
from .utils.split import split_code_into_sections

from .agent.sb_agent import agent

processing_order = ["models.py","views.py","urls.py"]

def getTemplateFileNames(path):
    file_paths = []
    for root, _, files in os.walk(path):
        for file in files:
            # Get the relative path to the base directory
            relative_path = os.path.relpath(os.path.join(root, file), path)
            file_paths.append(relative_path)
    return file_paths


def writeToFile(filePath,content,fileName):
    print("Saving to file ")
    dest = f"{filePath}/{fileName}"
    if os.path.exists(dest):
        # append to file
        with open(dest, "r+") as file:
            data = file.read()  # Step 1: Read existing content
        
            file.seek(0)        # Move to the beginning of the file
            file.truncate(0)    # Step 2: Clear the file

            write_data = f"{imports}\n{content}\n{data}"
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
        with open(filePath,"w") as file:
            file.write(content)

def getAppFileContent(appName,fileName,project_path):
    imports = []
    code = []

    fileToUpdate = fileName.split("/")[-1]
    filePath = f"{project_path}/{appName}/{fileToUpdate}"

    with open(fileName, "r") as file:
        data = file.read()
        data = split_code_into_sections(data)
        for chunk in data:
            if "import " in chunk:
                individualImports = getIndividualImports(chunk)
                imports.extend(individualImports)
            else:
                code.append(chunk)

    return [imports,code]


def processFile(fileName,appName,project_path):
    imports = []
    code = []

    with open(fileName,"r") as file:
        data = file.read()
        data = split_code_into_sections(data)
        for chunk in data:
            if "import " in chunk:
                individualImports = getIndividualImports(chunk)
                imports.extend(individualImports)
            else:
                code.append(chunk)
    

    fileImports, fileCode = getAppFileContent(appName,fileName,project_path)

    fileCode.extend(code)
    fileImports.extend(imports)

    fileCode = removeDuplicates(fileCode)
    fileImports = removeDuplicates(fileImports)

    importAsString = "\n".join(fileImports)
    codeAsString = "\n".join(fileCode)

    fileToUpdate = fileName.split("/")[-1]
    fileContent = importAsString + "\n\n" + codeAsString
    filePath = f"{project_path}/{appName}/"

    writeToFile(filePath,fileContent,fileToUpdate)

def getFeatureFromTemplate(template_path,project_root,template_name):
    """
    1) Ask for which app to implement feature. -- done
    2) Give feature information/description. -- pending
    3) Ask for Customization prompt and customize code. -- done
    4) Copy code and save in the right files (do proper refrencing).
    5) Give command to install feature dependencie and finish setup.
    6) Test
    """
    app_name = input("Which django app do you want to implement feature in : ")
    app_path = f"{project_root}/{app_name}"

    feature_name = template_path.split("/")[-1].split(".")[0]

    if os.path.exists(app_path) and os.path.isdir(app_path):
        print("\n\n------- Generating Feature -------\n\n")

        print(f"Getting template from {template_path}")

        # unpack template to .sb folder
        os.makedirs(f"{project_root}/.sb", exist_ok=True)
        template_unpack_path = f"{project_root}/.sb/{feature_name}"
        os.makedirs(template_unpack_path, exist_ok=True)

        # unpack
        print("Unpacking template")
        with zipfile.ZipFile(template_path, 'r') as zip_ref:
            zip_ref.extractall(template_unpack_path)

        # TODO: print feature description, along with dependencies and fields

        customize = input("would you like to customize feature (yes or no[default]) : ")
        customize = customize.strip()

        proceed_with_customization = False

        while True:
            if customize == "":
                break
            elif customize.lower() in ["yes","no"]:
                if customize.lower() == "yes" : proceed_with_customization = True
                break
            else:
                print("Enter a valid response")
                continue

        if proceed_with_customization:
            prompt = input("Enter Customization prompt (be as detailed as possible) : \n")
            # prompt = sys.stdin.read()

            # make agent call here
            # pass prompt and a list of all files in template
            files = getTemplateFileNames(template_unpack_path)
            print(files, " template files")
            res = agent(files,prompt,app_path,feature_name)
        else:
            path_to_template = f"{project_root}/.sb/{template_name}/kitchen"
            for file in os.listdir(path_to_template):
                file_path = f"{path_to_template}/{file}"
                print(file_path)
                processFile(file_path,app_name,project_root)
    else:
        print(f"No app with name {app_name} in {project_root}")
    
    return app_name

def convertFromTemplateToFeature(project_path,template_path,template_name):

    appName = getFeatureFromTemplate(template_path,project_path,template_name)

    template_root = f"{project_path}/.sb/{template_name}/kitchen"
    for file in os.listdir(template_root):
        processFile(f"{template_root}/{file}",appName,project_path)