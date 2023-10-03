from ts import *

if __name__ == "__main__":
    touchstone = Touchstone()

    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repo-root", default = pathlib.Path(".") / "../../Nictiz-testscripts")
    parser.add_argument("-f", "--properties-file", default = "properties.yml")
    parser.add_argument("--production", action = "store_true")
    parser.add_argument("target", nargs = "*", help = "The targets to execute (both numbers and mnemonics are supported)")
    args = parser.parse_args()

    known_targets = KnownTargets(args.repo_root, args.properties_file)

    if len(args.target) == 0:
        known_targets.list()
        print()
        folders = input("Please specify the folders to upload (space separated) ")
        folders = [folder.strip() for folder in folders.split(" ")]
    else:
        folders = args.target

    try:
        touchstone.loginFrontend()

        for folder_num in folders:
            target = known_targets.getUploadTarget(folder_num, "production" if args.production else "dev")
            touchstone.uploadTarget(target)

    finally:
        # Always try to logout, otherwise we'll have too many open sessions.
        touchstone.logoutFrontend()
