from ts import *

if __name__ == "__main__":
    launcher = Launcher()

    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repo-root", default = pathlib.Path(".") / "../../Nictiz-testscripts")
    parser.add_argument("-f", "--properties-file", default = "properties.yml")
    parser.add_argument("-l", "--list", help = "List all available targets", action = "store_true")
    parser.add_argument("--production", action = "store_true")
    parser.add_argument("target", nargs = "*", help = "The targets to execute (both numbers and mnemonics are supported)")
    args = parser.parse_args()

    known_targets = KnownTargets(args.repo_root, args.properties_file)

    if args.list:
        known_targets.list()
        exit(0)

    elif len(args.target) == 0:
        print("You need to specify at least one target (use --list to show the available targets)")
        exit(1)

    try:
        launcher.loginFrontend()

        for target_num in args.target:
            target = known_targets.getUploadTarget(target_num, "production" if args.production else "dev")
            launcher.uploadTarget(target)

    finally:
        # Always try to logout, otherwise we'll have too many open sessions.
        launcher.logoutFrontend()
