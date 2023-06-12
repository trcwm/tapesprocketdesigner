#!/usr/bin/python3
try:
    import toml
except:
    print("Please install the toml package")
    exit()

with open("pyproject.toml", "r") as f:
    data = f.read()
    tomlData = toml.loads(data)

    with open("tapesprocketdesigner/version.py", "w") as fout:
        fout.write("# Auto generated - do not change by hand\n\n")
        fout.write("version = \"{:s}\"\n".format(tomlData["project"]["version"]))
