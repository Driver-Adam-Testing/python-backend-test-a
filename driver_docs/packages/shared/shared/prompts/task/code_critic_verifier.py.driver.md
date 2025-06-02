# Purpose
This code defines a configuration for a system message, specifically for a process that involves analyzing and verifying the correctness of a given code snippet. The functionality is narrow, focusing on a structured approach to source verification, error detection, correction, and documentation. The code is essentially a configuration setup, consisting of a multi-line string `PROMPT` that outlines the steps for code analysis and a dictionary `MESSAGE` that pairs this prompt with a role identifier. This setup is likely used in a larger system where automated or semi-automated code review and correction are required, ensuring that any code snippet is thoroughly checked and documented for accuracy and correctness.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The variable `MESSAGE` is a dictionary with two key-value pairs: 'role' and 'content'. The 'role' key is assigned the string value 'system', and the 'content' key is assigned the value of the `PROMPT` variable, which is a multi-line string containing instructions for analyzing and correcting code snippets.
- **Use**: This variable is used to store and convey a structured message, likely for a system or application that processes or responds to code analysis tasks.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a multi-line string that provides detailed instructions for analyzing an input code snippet. It outlines steps for source verification, error detection, correction process, evidence documentation, and final reporting.
- **Use**: This variable is used to store a comprehensive set of guidelines for verifying and correcting code snippets, ensuring they are accurate and well-documented.


