def a():
    def b():
        return "abc"
    return b()

print(a)