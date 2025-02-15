import argparse
from pathlib import Path

from src.utils.split import split_code_into_sections
from src.feature_to_temp import create_temp_from_feature
from src.temp_to_feature import convertFromTemplateToFeature

from src.utils.yaml import read_yaml

"""
    convert from feature to template -- pending
    convert from template to feature -- pending
    argparser -- pending
    lang graph agent

    clean up - better clean up and refactoring
    deployment and packaging

    NOTE:
      - I need to add the template yaml file to zip file
      - find out why models is repeating itself
      - plus I need to append and not overwrite file when implementing features
"""

"""
    python speedbuild.py create - sb build . ./ManageRecipies.yaml
    python speedbuild.py feature . speed_build_ManageRecipes.zip

    sb <command> <project_root> <template|yaml root>
"""

def getAbsolutePath(relative_path):
    relative_path = Path(relative_path)
    absolute_path = relative_path.resolve()

    print(absolute_path)
    return str(absolute_path)

def createTemplate(args):
    project_root = getAbsolutePath(args.project_path)
    yaml_file_path = getAbsolutePath(args.template_path)

    # get project name from project root
    chunk = project_root.split("/")
    while chunk[-1] == "":
        chunk.pop()

    project_name = chunk[-1]

    data = read_yaml(yaml_file_path)
    print(data)

    create_temp_from_feature(
        project_root,
        project_name,
        data['feature'],
        project_root + data['feature_file_path']
    )

def implementFeature(args):
    project_root = getAbsolutePath(args.project_path)
    template_path = getAbsolutePath(args.template_path)

    template_name = template_path.split("/")[-1].replace(".zip","").strip()
    print(template_name)


    convertFromTemplateToFeature(project_root,template_path,template_name)

def main():
    # Create the top-level parser
    parser = argparse.ArgumentParser(description="Speed Build Command Line Interface")

      # Create subparsers for 'login' and 'project' commands
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # create
    create_parser = subparsers.add_parser('create', help="Create Template")
    create_parser.add_argument('-p', '--project_path', type=str, required=True, help="root folder of django project")
    create_parser.add_argument('-t', '--template_path', type=str, required=True, help="Path to feature YAML file")
    create_parser.set_defaults(func=None)

    # feature
    feature_parser = subparsers.add_parser('feature', help="Implement Feature From Template")
    feature_parser.add_argument('-p', '--project_path', type=str, required=True, help="root folder of django project")
    feature_parser.add_argument('-t', '--template_path', type=str, required=True, help="Path to speed build template")
    feature_parser.set_defaults(func=None)

    # Parse the arguments
    args = parser.parse_args()

    if args.command:
        if args.command == "create":
            print("creating template")
            createTemplate(args)
        elif args.command == "feature":
            print("implementing feature")
            implementFeature(args)
        else:
            parser.print_help()
    else:
        parser.print_help()


if __name__=="__main__":
    main()
