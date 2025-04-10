import random
import urllib.request

EFF_DICEWARE_URL = "https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt"


def load_eff_wordlist():
    with urllib.request.urlopen(EFF_DICEWARE_URL) as f:
        wordlist = []
        for line in f:
            parts = line.decode().strip().split()
            if len(parts) == 2:
                wordlist.append(parts[1])
        return wordlist


def generate_webhook_secret(num_words=16, delimiter=" "):
    wordlist = load_eff_wordlist()
    secret_words = random.choices(wordlist, k=num_words)
    return delimiter.join(secret_words)


if __name__ == "__main__":
    print(generate_webhook_secret())
