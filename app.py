import streamlit as st
import requests
import re
import json
import radon
from radon.metrics import mi_parameters
import openai
st.title("Github Code Analyser")


user_input = st.text_input("Enter github url here", "")

if st.button("Analyze code"):
    def fecth_respositories(github_url):
        # Extract the username from the GitHub URL
        username = github_url.split('/')[-1]

        # Make a GET request to the GitHub
        response = requests.get(f"https://api.github.com/users/{username}/repos")

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            repositories = response.json()

            # Extract the repository names and URLs
            repository_names = [repo['name'] for repo in repositories]
            repository_urls = [repo['html_url'] for repo in repositories]

            return repository_names, repository_urls

        else:
            print(f"Failed to fetch repositories. Status code: {response.status_code}")
            return [], []


    user_url = user_input
    repository_names, repository_urls = fecth_respositories(user_url)

    # Print the fetched repository names and URLs
    for name, url in zip(repository_names, repository_urls):
        print(f"Repository: {name}")
        print(f"URL: {url}")
        print()
    import shutil
    from git import Repo
    import os

    repository_dict = {}


    def clone_repository(repository_url, clone_path):
        Repo.clone_from(repository_url, clone_path)


    def get_all_files(folder_path):
        all_files = []
        for root, directories, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        return all_files


    # Clone and process each repository

    necessary_extensions = [".py", ".ini", ".md", ".txt", ".java", ".cpp", "ipynb"]


    def filter_necessary_files(files, necessary_extensions):
        necessary_files = [file for file in files if any(file.endswith(ext) for ext in necessary_extensions)]
        return necessary_files


    for repository_url in repository_urls:
        repository_name = repository_url.split("/")[-1].split(".")[0]  # Extract repository name from URL

        # Provide a unique clone path for each repository
        clone_path = f"{repository_name}"

        if os.path.exists(clone_path):
            shutil.rmtree(clone_path)  # Delete the existing clone directory

        # Clone the repository locally
        clone_repository(repository_url, clone_path)

        # Get all the files within the repository
        repository_files = get_all_files(clone_path)

        # Filter the repository files
        repository_files = filter_necessary_files(repository_files, necessary_extensions)

        # Print the collected files for the repository
        li = []
        print(f"Repository: {repository_name}")
        for file_path in repository_files:
            li.append(file_path)
        repository_dict[repository_name] = li

    final_dict = {}

    for repo_name in repository_dict:
        adv_dict = {}
        li = []
        li2 = []
        li3 = []

        for url in repository_dict[repo_name]:
            new = url.split('\\')

            if new[-1] == "requirements.txt":
                li.append(url)
            elif new[-1] == "README.md":
                li2.append(url)
            else:
                li3.append(url)

        adv_dict["requirements"] = li
        adv_dict["introduction"] = li2
        adv_dict["main_files"] = li3

        final_dict[repo_name] = adv_dict
    print(final_dict)


    def read_text_file(file_path):
        with open(file_path, 'r') as file:
            file_content = file.read()
        return file_content


    def preprocess_python_code(code):
        # Remove single-line comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)

        # Remove multi-line comments
        code = re.sub(r'"""[\s\S]*?"""', '', code, flags=re.MULTILINE)

        # Remove leading and trailing whitespace
        code = code.strip()

        return code


    def preprocess_cpp_code(code):
        # Remove single-line comments
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)

        # Remove multi-line comments
        code = re.sub(r'\/\*[\s\S]*?\*\/', '', code, flags=re.MULTILINE)

        # Remove leading and trailing whitespace
        code = code.strip()

        return code


    def preprocess_java_code(code):
        # Remove single-line comments
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)

        # Remove multi-line comments
        code = re.sub(r'\/\*[\s\S]*?\*\/', '', code, flags=re.MULTILINE)

        # Remove leading and trailing whitespace
        code = code.strip()

        return code


    def preprocess_ipynb_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            notebook_data = json.load(file)

        cells = notebook_data['cells']
        preprocessed_code = ""

        for cell in cells:
            if cell['cell_type'] == 'code':
                source = cell['source']

                # Combine code lines into a single string
                code = '\n'.join(source)

                # Remove code cell outputs
                cell['outputs'] = []

                # Remove comments from the code
                code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)

                # Normalize whitespace
                code = code.strip()

                # Append the preprocessed code to the result string
                preprocessed_code += code + "\n"

        return preprocessed_code


    def check_complexity(code):
        length_of_code = [len(code) for code in preprocessed_code_list]
        max_complexity_index = length_of_code.index(max(length_of_code))
        return max_complexity_index


    preprocessed_code_list = []  # List to store preprocessed code
    code_dict = {}

    final_code_dict = {}

    for repo_name in final_dict:
        code_dict = {}

        for sub_cate in final_dict[repo_name]:

            preprocessed_code_list = []

            for file_ in final_dict[repo_name][sub_cate]:
                file_path = file_

                # Preprocess the code based on file extension
                if file_path.endswith(".py"):
                    with open(file_path, 'r', encoding='utf-8') as file:
                        code = file.read()
                        preprocessed_code = preprocess_python_code(code)
                elif file_path.endswith(".txt"):
                    with open(file_path, 'r', encoding='utf-8') as file:
                        code = file.read()
                        preprocessed_code = code
                elif file_path.endswith(".md"):
                    with open(file_path, 'r', encoding='utf-8') as file:
                        code = file.read()
                        preprocessed_code = code
                elif file_path.endswith(".ipynb"):
                    preprocessed_code = preprocess_ipynb_file(file_path)

                preprocessed_code_list.append(preprocessed_code)

                max_complexity_index = check_complexity(code)

                code_dict[sub_cate] = preprocessed_code_list[max_complexity_index]

                code_dict["url"] = final_dict[repo_name][sub_cate][max_complexity_index]

        final_code_dict[repo_name] = code_dict


    def split_code_into_sections(code):
        # Define the pattern to split code into sections
        pattern = r"(?:(?:def|class)\s+\w+|^\s*#.*$\n )"

        # Split the code into sections using the pattern
        sections = re.split(pattern, code, flags=re.MULTILINE)

        # Remove any leading or trailing whitespace from each section
        sections = [section.strip() for section in sections if section.strip()]

        return sections


    # Print the sections
    # for repo_name in final_code_dict:
    #     sections = split_code_into_sections(final_code_dict[repo_name]['main_files'])
    #     final_code_dict[repo_name]['main_files'] = sections


    def calculate_complexity(code):
        try:
            cc = radon.metrics.mi_parameters(code)
            return cc
        except SyntaxError:
            return None


    def find_section_with_highest_complexity(code, num_lines):
        lines = code.split('\n')
        complexities = []

        for i in range(len(lines)):
            section = '\n'.join(lines[max(0, i - num_lines):i + num_lines + 1])
            complexity = calculate_complexity(section)
            if complexity is not None:
                complexities.append((complexity, i))

        if complexities:
            complexities.sort(reverse=True)
            line_number = complexities[0][1]
            return '\n'.join(lines[max(0, line_number - num_lines):line_number + num_lines + 1])
        else:
            return None

        return max_complexity_section


    for repo_name in final_code_dict:

        for i, section in enumerate(final_code_dict[repo_name]['main_files'], start=1):
            final_code_dict[repo_name]['main_files'] = find_section_with_highest_complexity(section, 5)


    def analyze_code_complexity(code):
        # Set up OpenAI API credentials
        openai.api_key = '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'

        # Define the prompt
        prompt = f"""I am giving you a dictionary of repositories in github which cotains all the information about 
        the different repository you need to tell which is the most difficult one and give the breif analysed 
        and give in this format 
        "name of the project: ,information about analysement: ,url: {user_input}"\n\n{code}"""

        # Generate completion using GPT
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.5
        )

        # Get the generated completion text
        completion_text = response.choices[0].text.strip()

        return completion_text


    complexity = analyze_code_complexity(final_code_dict)
    st.write(complexity)
#     def checkURL(str):
#
#         regex= 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
#         URL= re.findall(regex,str)
#         return URL
# # The driver code
#     final_url = "".join(checkURL(complexity))
#
#     new_file = final_url.insert(0,user_input)
#     file_ = new_file.split('/')
#     file_1 = file_[:-2]
#     st.write(file_1)

