# Purpose
This Python function, `build_modal_deploy_script`, generates a Bash script designed to automate the deployment of various content services across different environments. The function takes two parameters, `token_id` and `token_secret`, which are used to configure authentication for the deployment process. The generated script is structured to navigate through several directories, each corresponding to a different service, and uses the `poetry` tool to install dependencies and deploy the services using the `modal` command. This code provides narrow functionality, specifically tailored for deploying services in a structured environment, and is a utility function that outputs a deployment script rather than executing the deployment directly.
# Functions

---
### build_modal_deploy_script 
The function `build_modal_deploy_script` generates a bash script for deploying services to a specified environment using Modal and Poetry.
- **Inputs**:
    - `token_id`: A string representing the token ID used for authentication with Modal.
    - `token_secret`: A string representing the token secret used for authentication with Modal.
- **Control Flow**:
    - The function starts by defining a multi-line string `script` that contains a bash script.
    - The bash script begins with a shebang line for bash and sets the `-eo pipefail` option to ensure the script exits on errors.
    - It checks if an environment argument is provided; if not, it prints an error message and exits.
    - The environment argument is captured from the command line and echoed to the console.
    - The script sets the Modal token using the provided `token_id` and `token_secret`, and activates the `driver-ai` profile.
    - The script navigates to various directories (`inspector`, `agent`, `pdf_preprocessing`, `autodocs`) under `content_services`, installs dependencies using Poetry, and deploys the `src/main.py` file to the specified environment using Modal.
    - The function returns the constructed bash script as a string.
- **Output**:
    - A string containing the generated bash script for deploying services.


