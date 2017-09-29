from collections import deque

class Logger:
    def __init__(self):
        self.__info = deque([]);
        self.__status = {};
        self.__max_size = 10;

    def log(self, text):
        self.__info.append(text);
        while len(self.__info) > self.__max_size:
            self.__info.popleft();
        print(text);

    def status(self, name, value):
        self.__status[name] = value;

    def get_log(self):
        r = list(self.__info);
        return r;

    def get_status(self, name):
        return self.__status[name];

