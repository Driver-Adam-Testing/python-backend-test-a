class print_text_color:
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


class print_text_background:
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


class text_weight:
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class text_reset:
    ENDC = "\033[0m"


def print_dict(dict_to_print: dict):
    colors = [
        print_text_color.RED,
        print_text_color.GREEN,
        print_text_color.YELLOW,
        print_text_color.BLUE,
        print_text_color.MAGENTA,
        print_text_color.CYAN,
    ]
    keys = list(dict_to_print.keys())
    import hashlib

    def get_color_for_key(key):
        checksum = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return colors[checksum % len(colors)]

    for key in keys:
        color = get_color_for_key(key)
        print(f"{color}{key}: {dict_to_print[key]}{text_reset.ENDC}")
