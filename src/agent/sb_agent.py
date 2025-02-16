import json,os
from openai import OpenAI
from typing import Optional
from pydantic import BaseModel

from src.utils.split import split_code_into_sections
from src.utils.utils import getIndividualImports,removeDuplicates

from .system_prompt import system_prompt
from dotenv import load_dotenv


load_dotenv() 
client = OpenAI()

memory = [
    {"role": "system", "content": system_prompt},
]


class SpeedBuildFormat(BaseModel):
    status: str
    action: str
    file_name: str
    content: Optional[str] = None 
    comment: Optional[str] = None 


def foramtLLMOutput(AI_response):
    AI_response = AI_response.replace("```json","").replace("```","")
    AI_response = AI_response.strip()
    print(AI_response)
    return json.loads(AI_response)


def makeLLMCall(user_input):
    memory.append({"role": "user","content": user_input})
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=memory,
        response_format=SpeedBuildFormat,
    )

     # Extract the assistant's response
    assistant_response = completion.choices[0].message.parsed #completion.choices[0].message.content

    # Add the assistant's response to memory
    memory.append({"role": "assistant", "content": f"{assistant_response.file_name} : {assistant_response.action} \n {assistant_response.content}"})

    return assistant_response

def getFileContent(filePath,fileName,template_name)->str:
    dest = f"{filePath}/.sb/{template_name}/{fileName}"
    print("file ",dest)
    if os.path.exists(dest):
        with open(dest, "r") as file:
            data = file.read()
            return data 
    else:
        return "File Does Not Exist"


def writeToFile(filePath,content,fileName):
    dest = f"{filePath}/{fileName}"
    print("Saving to file ",dest)
    if os.path.exists(dest):
        # append to file
        with open(dest, "r+") as file:
            data = file.read()  # Step 1: Read existing content
        
            file.seek(0)        # Move to the beginning of the file
            file.truncate(0)    # Step 2: Clear the file

            write_data = f"{content}\n{data}"
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
            file.write(content)

def agent(files,prompt,project_root,template_name):
    file_processed = set()
    read_path = project_root.split("/")
    read_path.pop()
    read_path = "/".join(read_path)
    print("readd path is ", read_path)

    while len(file_processed) < len(files):
        prompt = prompt + "\n" + f"files : {files}"
        response = makeLLMCall(prompt)
        
        status = response.status
        file_name = response.file_name
        action = response.action

        print(f"{file_name} : {action}")
        
        if status == "request_file":
            file_content = getFileContent(read_path,file_name,template_name)
            prompt = file_content
            
        elif status == "success":
            code_content = response.content
            comment = response.comment

            file_name = file_name.split("/")[-1]
            writeToFile(project_root,code_content,file_name)
            print(f"{file_name} : {comment}")
            # add file_name to file_processed
            file_processed.add(file_name)
            prompt = "next"
            
        continue