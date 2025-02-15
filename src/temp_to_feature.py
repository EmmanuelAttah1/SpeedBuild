import os, zipfile
from .utils.utils import getIndividualImports
from .utils.split import split_code_into_sections

processing_order = ["models.py","views.py","urls.py"]

def removeDuplicates(code):
    cleaned_code = []
    for line in code:
        if line not in cleaned_code:
            cleaned_code.append(line)

    return cleaned_code


def writeToFile(filePath,content):
    print("Saving to file ")
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
    filePath = f"{project_path}/{appName}/{fileToUpdate}"

    writeToFile(filePath,fileContent)

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

        if proceed_with_customization:
            prompt = input("Enter Customization prompt (be as detailed as possible) : \n")

            # make agent call here
        
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