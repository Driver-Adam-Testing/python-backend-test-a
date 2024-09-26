PROMPT = """
Remove congratulatory language from the text.
Remove language from the text that uses words that describes and congratulates the social qualities of a technical product. Sentences that qualify often include words that in the language families of "pivotal", "essential", "critical", "robust", "integral". "rigorous", "comprehensive", and "valuable", "meticulously", "vital", and "exemplified".
Remove text that is extremely generic.
Remove text that is redundant.
"""

MESSAGE = {"role": "system", "content": PROMPT}
