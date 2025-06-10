1. Setup [GitHub CLI](https://cli.github.com/)

Ensure that you are login to your GitHub account in the CLI.

2. Install [Python](https://www.python.org/downloads/)

Ensure that the `Add python.exe to PATH` is checked

3. Setup python virtual environment.
```ps
// Install virtualenv package
pip install virtualenv

// Create a virtual environment.
python -m venv venv

// Activate virtual environment
.\venv\Scripts\activate

// Install required packages
pip install -r requirements.txt

// Deactivate virtual environment
deactivate
```

4. Create the executable file.
```ps
pyinstaller --onefile ./backup.py
```

5. Run the backup.exe

The file is located at dist/backup.exe

Running tests
```ps
python -m unittest discover -s tests
```
