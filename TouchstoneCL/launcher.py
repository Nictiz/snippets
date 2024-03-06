from ts import *

if __name__ == "__main__":
    touchstone = Touchstone()

    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repo-root", default = pathlib.Path(".") / "../../Nictiz-testscripts")
    parser.add_argument("-f", "--properties-file", default = "properties.yml")
    parser.add_argument("--production", action = "store_true")
    parser.add_argument("-T", help = f"Date T to use (default is '{touchstone.date_T}')")
    parser.add_argument("--start-only", action = "store_true", help = "Just launch the executions, don't wait for them to finish and don't report the results, unless it's explicitly defined that an execution should finish before continuing")
    parser.add_argument("--jira-table", action = "store_true", help = "Print a summary in Jira ;ost format after completion (ignored if --start-only is provided)")
    parser.add_argument("target", nargs = "*", help = "The targets to execute (both numbers and mnemonics are supported)")
    args = parser.parse_args()

    known_targets = KnownTargets(args.repo_root, args.properties_file)

    if args.T != None:
        touchstone.date_T = args.T
    touchstone.start_only = args.start_only

    if len(args.target) == 0:
        known_targets.list(exclude_reference=True)
        print()
        folders = input("Please specify the folders to execute (space separated) ")
        folders = [folder.strip() for folder in folders.split(" ") if folder.strip() != ""]
    else:
        folders = args.target

    try:
        touchstone.loginFrontend()

        targets = [known_targets.getExecutionTarget(folder_num, "production" if args.production else "dev") for folder_num in folders]
        touchstone.executeTargets(targets, args.start_only)

        if not args.start_only and args.jira_table:
            print("### Jira list ###")
            for execution in touchstone.executions:
                line = "* "
                if execution.fails > 0:
                    line += "❌"
                elif execution.warns > 0:
                    line += "⚠️"
                else:
                    line += "✅"
                line += f" [{execution.target.rel_path}](https://touchstone.aegis.net/touchstone/execution?exec={execution.execution_id})"
                if execution.fails > 0 or execution.warns > 0:
                    line += ": "
                    if execution.fails > 0:
                        line += f"{execution.fails} x failures"
                        if execution.warns > 0:
                            line += ", "
                    if execution.warns > 0:
                        line += f"\n{execution.warns} x warning"
                print(line)

    finally:
        # Always try to logout, otherwise we'll have too many open sessions.
        touchstone.logoutFrontend()
