import re


class Formatter:

    def process_line(self, line: str):
        escaped = False
        last_char = None
        return_list = []
        buffer = []

        for c in line:
            if c == '|':
                if escaped:
                    buffer.append('|')
                    escaped = False
                else:
                    if len(buffer) > 0:
                        return_list.append(''.join(buffer))
                        buffer = []
            elif c == '\\':
                if escaped:
                    buffer.append('\\')
                    escaped = False
                else:
                    escaped = True
            else:
                if escaped:
                    buffer.append('\\')
                    escaped = False
                buffer.append(c)

            last_char = c

        if len(buffer) > 0:
            return_list.append(''.join(buffer))
            buffer = []

        return return_list

    def build_table(self, input_str: str):
        table = []

        lines = input_str.splitlines()

        for line in lines:
            table.append(self.process_line(line))

        return table


if __name__ == '__main__':
    test_str = (
        '|a|b\\\\|c|\n'
        '|-|-|-|\n'
        '|c|3|w|\n'
        '| a| d |1|\n'
    )

    print(test_str)

    formatter = Formatter()

    table = formatter.build_table(test_str)
    print(table)
