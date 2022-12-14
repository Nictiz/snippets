# Scripts for rearranging repository's

This is a collection of scripts that have been used to migrate and split Subversion and git repository's. These scripts can be used as inspiration for when such an operation needs to be done again. The rationale for rewriting a repo, rather than simply copying the files you need to a new situation, is that the development history is kept. There are some minor nuisances, like tags being present that have lost their meaning. This could probably be fixed as well, but the problem was too small to invest time in this.

*Note*: This is a dump of historical files found on my computer. For some reason, some commands are commented out. I just left it at that, as these scripts are only meant as inspiration.

The scripts are all Bash shell scripts with the following additional software:
* git, obviously
* [git-filter-repo](https://github.com/newren/git-filter-repo), which does the actual rewriting.

They do the following things:
* Remove things (also from history) that are not relevant to the new situation.
* Move folders and files to a new location.
* Remove irrelevant branches.
* Rename branches.

The following scripts are included:
* split-Beelden.sh: Used to split out the Beelden/Images specific conformance resources from the Zib2017-repo to its own repo.
* split-BgZ.sh: Used to split out the BgZ specific conformance resources from the Zib2017-repo to its own repo.
* split-eAfspraak.sh: Used to split out the eAfspraak specific conformance resources from the Zib2017-repo to its own repo.
* split-MP.sh/split-MP2.sh: Used to split out the Medication specific conformance resources from the Zib2017-repo to its own repo. Why there are two files, is lost in the mists of time.
* split-Generate.sh/split-testscripts-dev.sh: Used to split out tooling present in the Nictiz-STU3-testscripts repo to a separate repo, and in the original repo include it again as subtree.
* Migratie-HL7-mappings.md: A description on the migration of CloudForge/SVN to git for the HL7-mappings repo. It is not a script, but it includes the relevant commands.