

## LoglineLeviathan // Analyze/Export-Module

## **Installation**

### Windows:

Currently no .exe available yet. Follow the below Linux Instructions and adapt to your Windows shell.

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

### Analysis:

> On startup, a new database will be created by default and populated with the available entities. If a database from a prior session is present, it will be used.

After startup, no files are selected for ingestion. Starting from there, you have the following possibilities:

-   Select files with "Add Files to Selection": Opens a file browser and lets you select one or more files.
    
-   Choose directory with "Add Directory and Subdirectories": Recursively adds all files in all subdirectories of .
    

> Resetting the file selection is only possible via the "Clear Files from Selection"-Button.

-   Choose existing database. 
    

Button "Start/Resume File Analysis" strats the file ingestion and database population.
