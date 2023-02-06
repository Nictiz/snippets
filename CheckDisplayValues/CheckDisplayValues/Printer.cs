using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CheckDisplayValues
{
    public class Printer
    {
        public const string WARNING = "WARNING";
        public const string ERROR = "ERROR";
        public bool firstMessage = true;

        private string fileName;
        private int warningCount;
        private int errorCount;

        /// <summary>
        /// Class that compares all analyzes all DisplayValues and prints any inconsistencies
        /// </summary>
        /// <param name="fileName"></param>
        public Printer(string fileName)
        {
            this.fileName = fileName;
            this.warningCount = 0;
            this.errorCount = 0;
            firstMessage = true;
        }

        /// <summary>
        /// Goes trhrough all codes in a file and then checks if the current display value is allowed.
        /// </summary>
        /// <param name="displayValues"></param>
        public Tuple<int, int> PrintInconsistency(List<DisplayValue> displayValues)
        {
            warningCount = 0;
            errorCount = 0;

            //for every code in the file
            foreach (DisplayValue displayValue in displayValues)
            {
                if(displayValue.system == FileChecker.NOTFOUNDINPACKAGE)
                {
                    PrintMessage(null,null, displayValue.code);
                }
                // Currently set to false as this displays a message if the current display value is not identical to the ZiB value
                else if (displayValue.IsZiBValueSet() && false)
                {
                    PrintMessage(displayValue.displayCurrent, displayValue.displayCorrect.First(x => x.Use == "ZiB").Display, displayValue.code, true);
                }
                else
                {
                    List<Translation> dutchTranslations = displayValue.GetDutchDisplayValues();
                    List<Translation> englishTranslations = displayValue.GetEnglishDisplayValues();

                    if (dutchTranslations != null)
                    {
                        if (!dutchTranslations.Any(x => x.Display.ToLower() == displayValue.displayCurrent.ToLower()))
                        {
                            PrintMessage(displayValue.displayCurrent
                                , (dutchTranslations.Find(t => t.Use == "ZiB") ?? dutchTranslations.Find(t => t.Use == "display") ?? dutchTranslations.Find(t => t.Use == "Preferred For Language") ?? dutchTranslations.Find(t => t.Use == "Fully specified name"))?.Display ?? ""
                                , displayValue.code);
                        }
                    }
                    else if (englishTranslations != null)
                    {
                        if (!englishTranslations.Any(x => x.Display.ToLower() == displayValue.displayCurrent.ToLower()))
                        {
                            PrintMessage(displayValue.displayCurrent
                                , (dutchTranslations.Find(t => t.Use == "ZiB") ?? englishTranslations.Find(t => t.Use == "display") ?? englishTranslations.Find(t => t.Use == "Preferred For Language") ?? englishTranslations.Find(t => t.Use == "Fully specified name"))?.Display ?? ""
                                , displayValue.code);
                        }
                    }
                    else
                    {
                        PrintMessage(displayValue.displayCurrent
                                , ""
                                , displayValue.code);
                    }
                }
            }
            return new Tuple<int, int>(warningCount,errorCount);
        }

        /// <summary>
        /// Print message if strings are not equal
        /// </summary>
        /// <param name="original"></param>
        /// <param name="nts"></param>
        /// <param name="code"></param>
        private void PrintMessage(string original, string nts, string code, bool ZiB = false)
        {
            if (this.firstMessage)
            {
                Console.WriteLine($"\t{fileName}: ");
                this.firstMessage = false;
            }

            if(original == null)
            {
                PrintWarningError(Printer.WARNING);
                Console.WriteLine($"\tCould not find {code}");
                warningCount++;
            }
            else if (original.ToLower() != nts.ToLower())
            {
                if (nts.Equals(""))
                {
                    PrintWarningError(Printer.WARNING);
                    Console.Write($"No translation available for code \"{code}\", please check manually");
                    warningCount++;
                }
                else
                {
                    PrintWarningError(Printer.ERROR);
                    Console.Write($"{code}:\"{original}\" Should be:\"{nts}\" ");
                    if (ZiB)
                    {
                        Console.Write("According to the ZiB");
                    }
                    errorCount++;
                }
                Console.WriteLine("");
            }
        }

        private static void PrintWarningError(string level)
        {
            if (level == Printer.WARNING)
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.Write("\t\tWARNING: ");
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.Write("\t\tERROR: ");
            }

            Console.ResetColor();
        }

        public static void PrintStats(List<string> standardNameList, Tuple<int, int> results, NTS nts)
        {
            Console.WriteLine();
            Console.WriteLine("Done");
            Console.WriteLine($"Out of the {nts.totalSNOMEDLookups} SNOMED lookups, {nts.savedSNOMEDLookups} were already done before");

            Console.WriteLine("Standards containing errors or warnings:");
            foreach(string name in standardNameList)
            {
                Console.WriteLine(name);
            }
            Console.WriteLine();
            Console.Write($"Total amount of ");
            PrintWarningError(Printer.WARNING);
            Console.WriteLine($" {results.Item1}");
            Console.Write($"Total amount of ");
            PrintWarningError(Printer.ERROR);
            Console.WriteLine($" {results.Item2}");

            if (!nts._connected)
            {
                Console.WriteLine("Please keep in mind that the NTS was not used due to an earlier error. All warnings and errors need to be checked manually.");
            }
        }
    }
}
