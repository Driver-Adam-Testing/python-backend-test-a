PROMPT = """I am a seasoned software engineer, I seek in-depth technical documentation on specific subjects. I am keen on exploring advanced topics such as technical enhancements, explaination and analysis, and code examples, and assessments under various conditions. I expect to see examples. I expect a thorough examination, and I expect content pertaining to only the codebase I'm examining. I NEVER want generalized information unless it's directly relevant to my documentation."""
MESSAGE = {"role": "user", "content": PROMPT}
ASSISTANT_MESSAGE = {
    "role": "assistant",
    "content": """Understood. When you inquire about specific technical subjects, I'll provide detailed responses tailored to your expertise level, focusing on advanced topics, technical enhancements, in-depth explanations, analyses, code examples, and assessments under various conditions. I'll ensure that the information is directly relevant to the specific codebase or technology you're examining and avoid generalizations unless they're directly applicable to your context.
If you have a particular topic or technology in mind, please feel free to share more details, and I'll do my best to meet your expectations with precise, technical, and in-depth information.""",
}
