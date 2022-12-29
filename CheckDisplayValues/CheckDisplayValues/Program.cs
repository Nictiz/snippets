using Microsoft.Extensions.Configuration;

namespace CheckDisplayValues
{
    public class Program
    {
        public static void Main()
        {
            DirectoryInfo packages = new DirectoryInfo("..\\..\\..\\Packages");

            string? dir = Directory.GetCurrentDirectory();
            string? parent = Directory.GetParent(dir ?? "C:/")?.Parent?.Parent?.FullName;
            IConfigurationRoot MyConfig = new ConfigurationBuilder().AddJsonFile($"{parent}/appsettings.json").Build();

            string? testscriptDir = MyConfig.GetValue<string>("AppSettings:Nictiz-testscripts-dir");
            DirectoryInfo testscripts = new DirectoryInfo(testscriptDir ?? "");

            FileChecker fileChecker = new FileChecker();

            //for every informationstandard
            if (testscripts.Exists)
            {
                DirectoryInfo dev = new DirectoryInfo(testscriptDir + "\\dev");

                foreach (DirectoryInfo subDir in dev.GetDirectories())
                {
                    if(subDir.Name.Contains("FHIR3") && (subDir.Name.Contains("-Cert")/* || subDir.Name.Contains("-Test")*/)) // TODO Test toevoegen?
                    {
                        foreach(DirectoryInfo standard in subDir.GetDirectories())
                        {
                            CheckStandards(fileChecker, standard, packages);
                        }
                    }
                }
            }
            else
            {
                Console.WriteLine("Could not find dir");
                throw new DirectoryNotFoundException();
            }

            Console.WriteLine($"Out of the {fileChecker.nts.totalSNOMEDLookups} SNOMED lookups, {fileChecker.nts.savedSNOMEDLookups} were allready done before");
        }

        private static void CheckStandards(FileChecker fileChecker, DirectoryInfo standard, DirectoryInfo packages)
        {
            switch (standard.Name)
            {
                //TODO add all standards
                case "BgZ-3-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources"), packages, standard.Name);
                    break;
                case "eAppointment-2-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources"), packages, standard.Name);
                    break;
                case "GenPractData-2-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources-query-send"), packages, standard.Name + " (query-send)");
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources-generic"), packages, standard.Name + " (generic)");
                    break;
                case "BgLZ-3-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources"), packages, standard.Name);
                    break;
            }
        }

        private static void CheckFolder(FileChecker fileChecker, DirectoryInfo d, DirectoryInfo packages, string fileName)
        {
            Console.WriteLine($"Now Checking \"{fileName}\"");

            List<string> packageNames = new();

            foreach (FileInfo package in packages.GetFiles("*.tgz"))
            {
                packageNames.Add(package.FullName);
            }

            foreach (FileInfo file in d.GetFiles("*.xml"))
            {
                fileChecker.CheckFile(file, packageNames);
            }
        }
    }
}