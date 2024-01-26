

## LoglineLeviathan // Analyze/Export-Module

## **Installation**

### Windows:

Currently no .exe available yet. Follow the below Linux Instructions and adapt to your Windows shell.
If you installed via pip install -r requirements.txt, you should run
```
pip uninstall python-magic
pip install python-magic-bin==0.4.14
```
afterwards.

> Important: The directories "data" with the entities.yaml and "output" need to be present.

### Linux / Python-Sourcecode:

This guide applies to building the application from source on a Linux host.

1.  Required prerequisites: python3 (3.11 or newer), python3-pip and python3.11-venv (or whatever version you have), git.
    
2.  Clone the git repository:

    git clone https://github.com/overcuriousity/LoglineLeviathan
    
3.  Shell:
    
    ```
    cd LoglineLeviathan && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
    ```
    
4.  Start:
    
    ```
    python3 run.py
    ```
    

## **Usage**



> On startup, a new database will be created by default and populated with the available entities. If a database from a prior session is present, it will be used.

After startup, no files are selected for ingestion. Starting from there, you have the following possibilities:

-   Select files with "Add Files to Selection": Opens a file browser and lets you select one or more files.
    
-   Choose directory with "Add Directory and Subdirectories": Recursively adds all files in all subdirectories of .
    

> Resetting the file selection is only possible via the "Clear Files from Selection"-Button.

-   Choose existing database. 
    

Button "Start/Resume File Analysis" strats the file ingestion and database population.

After that, you can proceed further, making searches with the integrated search engine, gnerate a report or a wordlist (which could also be used for parsing).

## **Customization**

The big strength of this application is, that it can be easily be expanded with additional analysis methods with minimal effort. Just append the yaml file in ./data/entities.yaml with entries by the given structure, and add the corresponding scripts in ./data/parser if desired. The GUI elements will show up automatically.