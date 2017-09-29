import sys
from collections import deque

class Console:
    def __init__(self, description=""):
        self.__history = deque();
        self.__history.append("CONSOLE: {}".format(description));
        self.__cur_cmd = "";
        self.__cmd_history= [];
        self.__cmd_ptr = 0;
        self.__prompt = "> "
        self.__max_lines = 30;
        self.__commands = {};
        self.register_cmd("help", self.__help, "show available commands");
        self.register_cmd("clear", self.__clear, "clear history");

    def get_text(self):
        display_text = list(self.__history);
        display_text.append(self.__prompt + self.__cur_cmd)
        return display_text[-self.__max_lines:];

    def register_cmd(self, cmd, func, description=""):
        self.__commands[cmd] = (func, description);

    def keyboard(self, key):
        ascii_key = ord(key);
        if ascii_key == 13 or ascii_key == 3: # enter
            self.__exec_command();
            self.__clear_cmd();
        elif ascii_key == 127: # backspace
            if len(self.__cur_cmd) > 0:
                self.__cur_cmd = self.__cur_cmd[:-1];
        #elif ascii_key == 38: # up
        #    num_cmds = len(self.__cmd_cmd);
        #    self.__cmd_ptr + 1;
        #    self.__cmd_ptr = max(0, self.__cmd_ptr);
        #    self.__cmd_ptr = min(num_cmds-1, self.__cmd_ptr);
        #    self.__cur_cmd = self.__cmd_history[num_cmds-1-self.__cmd_ptr];
        else:
            self.__cur_cmd += key.decode("utf-8");

    def __exec_command(self):
        self.__history.append(self.__prompt + self.__cur_cmd);
        self.__cmd_history.append(self.__cur_cmd);
        fields = self.__cur_cmd.split();
        if len(fields) == 0: return;
        if fields[0] not in self.__commands:
            err = "error: command \"{}\" not found".format(fields[0]);
            self.__history.append(err);
        else:
            cmd = self.__commands[fields[0]][0];
            result = cmd(*fields[1:]);
            if isinstance(result, str):
                result = result.split("\n")
            if isinstance(result, list):
                self.__history.extend(result);

    def __clear_cmd(self):
        self.__cur_cmd = "";
        self.__cmd_ptr = 0;

    def __help(self, target_cmd=None):
        if target_cmd is None:
            self.__history.append("  {:<10} {}".format("<command>", "<description>"));
            for cmd_name in self.__commands:
                desc = self.__commands[cmd_name][1];
                self.__history.append(": {:<10} {}".format(cmd_name, desc));
            self.__history.append("use help [cmd] to see detail helps");
        else:
            if target_cmd not in self.__commands:
                return "error: command {} not found".format(target_cmd);
            doc = self.__commands[target_cmd][0].__doc__
            if doc is not None:
                doc = self.trim(doc)
                doc = doc.split("\n");
                self.__history.extend(doc);
            else:
                self.__history.append("no further help available");

    def trim(self, docstring):
        """
        uniformly trim off the indentation of doc string
        copied from http://www.python.org/dev/peps/pep-0257/
        """
        if not docstring:
            return ''
        # Convert tabs to spaces (following the normal Python rules)
        # and split into a list of lines:
        lines = docstring.expandtabs().splitlines()
        # Determine minimum indentation (first line doesn't count):
        indent = sys.maxint
        for line in lines[1:]:
            stripped = line.lstrip()
            if stripped:
                indent = min(indent, len(line) - len(stripped))
        # Remove indentation (first line is special):
        trimmed = [lines[0].strip()]
        if indent < sys.maxint:
            for line in lines[1:]:
                trimmed.append(line[indent:].rstrip())
        # Strip off trailing and leading blank lines:
        while trimmed and not trimmed[-1]:
            trimmed.pop()
        while trimmed and not trimmed[0]:
            trimmed.pop(0)
        # Return a single string:
        return '\n'.join(trimmed)

    def __clear(self):
        self.__history.clear();

