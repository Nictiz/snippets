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

            NTS nts = new();
            FileChecker fileChecker = new FileChecker(nts);

            List<string> standardWarningNameList = new();
            int warningCount = 0;
            int errorCount = 0;

            //for every informationstandard
            if (testscripts.Exists)
            {
                DirectoryInfo dev = new DirectoryInfo(testscriptDir + "\\dev");

                foreach (DirectoryInfo subDir in dev.GetDirectories())
                {
                    if(subDir.Name.Contains("FHIR3") && (subDir.Name.Contains("-Cert")/* || subDir.Name.Contains("-Test")*/)) // TODO add Test?
                    {
                        // Check every standard
                        foreach(DirectoryInfo standard in subDir.GetDirectories())
                        {
                            CheckStandards(fileChecker, standard, packages);

                            // If a warning or error was found, register them for later analysis.
                            if(fileChecker.warningCount > 0 || fileChecker.errorCount > 0)
                            {
                                standardWarningNameList.Add(standard.Name);
                                warningCount += fileChecker.warningCount;
                                errorCount += fileChecker.errorCount;
                                fileChecker.warningCount = 0;
                                fileChecker.errorCount = 0;
                            }
                        }
                    }
                }
            }
            else
            {
                Console.WriteLine("Could not find dir");
                throw new DirectoryNotFoundException();
            }

            // Wrapping up by printing some stats
            Printer.PrintStats(standardWarningNameList, new Tuple<int, int>(warningCount, errorCount), nts);
        }

        private static void CheckStandards(FileChecker fileChecker, DirectoryInfo standard, DirectoryInfo packages)
        {
            switch (standard.Name)
            {
                //TODO add all standards
                case "AllergyIntolerance-3-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\AllergyIntolerance20"), packages, standard.Name + " (AllergyIntolerance20)");
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\AllergyIntoleranceConv"), packages, standard.Name + " (AllergyIntoleranceConv)");
                    break;
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
                case "GGZ-2-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources"), packages, standard.Name);
                    break;
                case "Images-2-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\transaction-bundles"), packages, standard.Name);
                    break;
                case "LaboratoryResults-2-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources-generic"), packages, standard.Name + " (generic)");
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources-query-send"), packages, standard.Name + " (query-send)");
                    break;
                case "PDFA-3-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources"), packages, standard.Name);
                    break;
                case "Questionnaires-2-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources\\resources-generic"), packages, standard.Name + " (generic)");
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources\\resources-questionnaires"), packages, standard.Name + " (questionnaires)");
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources\\resources-specific"), packages, standard.Name + " (specific)");
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources\\minimum"), packages, standard.Name + " (minimum)");
                    break;
                case "SelfMeasurements-2-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources-generic"), packages, standard.Name + " (generic)");
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources-query-send"), packages, standard.Name + " (query-send)");
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources-serve-receive"), packages, standard.Name + " (serve-receive)");
                    break;
                case "BgLZ-3-0":
                    CheckFolder(fileChecker, new DirectoryInfo(standard.FullName + "\\_reference\\resources"), packages, standard.Name);
                    break;
            }
        }

        private static void CheckFolder(FileChecker fileChecker, DirectoryInfo d, DirectoryInfo packages, string fileName)
        {
            Console.WriteLine();
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