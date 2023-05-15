# NinjaGen
Generate [ninja](https://ninja-build.org) build file
from YAML project file for [XcodeGen](https://github.com/yonaskolb/XcodeGen).

## Requirements
python3 with pyaml.

## Installation
On macOS using homebrew:
```
brew install python
pip3 install pyaml
```

## Usage
In a directory that contains `project.yaml` run
```
python3 ninjagen.py 
```

In any other directory (or to process project file with diferent name) run
```
python3 ninjagen.py path/to/project.yaml
```

It will create a build.ninja file in the current directory.

Then run `ninja` to build the project.

## Limitations
Currently the script has very limited functionality.
Only small subset of XcodeGen features is supported.
