
# FlexiQuery
*[WIP]A modular framework which is meant to process large amounts of unstructured data and export it afterwards.*

This repository remains in concept state until further development.

**The concept aims to unify my other projects, analyze_export and mass_ip_analysis, into a sophisticated python application which is highly modular and easy to expand.**

## Aim
The application is aimed to all persons which are interested in OSINT, network forensics, data science and crypto-ivestigations.
It is explicitly not aimed to support any criminal activities.

## Concept
The application will consist of three main scripts:

 1. Entity parser

> The entity parser will ingest any mass of unstructured data delivered in any format. It will heavily utilize regex, which can be expanded or customized by the operator, to parse a that dataset for the desired entities and fill a SQLite database wit it.

2. GUI

> The GUI intends to control the other parts, enabling also persons who aren´t comfortable with using the CLI to operate it. Also, a GUI enables to present the operator with the options available on a glance.
> The GUI will either be a Django-based webinterface or simplistic PyQt application. Almost certainly it will also support CLI-based operation.

3. Processor/Composer

> The processor will, after customized via GUI, query the database for specific entities, doing any operation with them which can be defined by small python scripts (plugins) which can quickly be assembled with low-level coding skills. Also implementation of individual APIs, owned by the operator, is possible, while these won´t be part of this repository for obvious reasons.
> After processing, a customized report is produces as configured via GUI.
> All this will be handled by one or more custom python scripts which call the plugins as modules.

The application will follow these guidelines:

 - accessability
 - modularity
 - datasource-transparency

## Contribution
As I consider myself still a beginner, recommendations and ideas are welcome. Feel free to contribute via GitHub or personal contact.

## License
The repository will be published under the GNU license. No monetarization ore closed-source development is planned for this repository as long as maintained on GitHub.
