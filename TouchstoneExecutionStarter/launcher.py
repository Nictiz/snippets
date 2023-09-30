from ts import *

if __name__ == "__main__":
    launcher = Launcher()

    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repo-root", default = pathlib.Path(".") / "../../Nictiz-testscripts")
    parser.add_argument("-f", "--properties-file", default = "properties.yml")
    parser.add_argument("-l", "--list", help = "List all available targets", action = "store_true")
    parser.add_argument("--production", action = "store_true")
    parser.add_argument("-T", help = f"Date T to use (default is '{launcher.date_T}')")
    parser.add_argument("--start-only", action = "store_true", help = "Just launch the executions, don't wait for them to finish and don't report the results, unless it's explicitly defined that an execution should finish before continuing")
    parser.add_argument("--jira-table", action = "store_true", help = "Print a summary in Jira table format after completion (ignored if --start-only is provided)")
    parser.add_argument("target", nargs = "*", help = "The targets to execute (both numbers and mnemonics are supported)")
    args = parser.parse_args()

    known_targets = KnownTargets(args.repo_root, args.properties_file)

    if args.T != None:
        launcher.date_T = args.T
    launcher.start_only = args.start_only
    launcher.jira_table_summary = args.jira_table

    if args.list:
        known_targets.list(exclude_reference=True)
        exit(0)

    elif len(args.target) == 0:
        print("You need to specify at least one target (use --list to show the available targets)")
        exit(1)

    try:
        launcher.loginFrontend()

        targets = []
        for target_num in args.target:
            targets.append(known_targets.getExecutionTarget(target_num, "production" if args.production else "dev"))

        launcher.executeTargets(targets, args.start_only)
        if not args.start_only and args.jira_table:
            print("### Jira table ###")
            for execution in launcher.executions:
                line =  f"|{execution.target.rel_path}|"
                line += "(/)" if execution.status == "Passed" else "(x)"
                if execution.fails > 0:
                    line += f"\n{execution.fails} x failures"
                if execution.warns > 0:
                    line += f"\n{execution.warns} x warning"
                line += f"| | |[https://touchstone.aegis.net/touchstone/execution?exec={execution.execution_id}]|"
                print(line)

    finally:
        # Always try to logout, otherwise we'll have too many open sessions.
        launcher.logoutFrontend()
