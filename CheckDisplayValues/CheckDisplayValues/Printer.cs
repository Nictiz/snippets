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

        string fileName;
        bool firstMessage = true;

        public Printer(string fileName)
        {
            this.fileName = fileName;
            this.firstMessage = true;
        }

        /// <summary>
        /// Goes trhrough all codes in a file and then checks if the current display value is allowed.
        /// </summary>
        /// <param name="displayValues"></param>
        public void PrintInconsistency(List<DisplayValue> displayValues)
        {
            //for every code in the file
            foreach (DisplayValue displayValue in displayValues)
            {
                if(displayValue.system == "Validation")
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
                                , (dutchTranslations.Find(t => t.Use == "ZiB") ?? dutchTranslations.Find(t => t.Use == "display") ?? dutchTranslations.Find(t => t.Use == "Fully specified name") ?? dutchTranslations.Find(t => t.Use == "Preferred For Language"))?.Display ?? ""
                                , displayValue.code);
                        }
                    }
                    else if (englishTranslations != null)
                    {
                        if (!englishTranslations.Any(x => x.Display.ToLower() == displayValue.displayCurrent.ToLower()))
                        {
                            PrintMessage(displayValue.displayCurrent
                                , (dutchTranslations.Find(t => t.Use == "ZiB") ?? englishTranslations.Find(t => t.Use == "display") ?? englishTranslations.Find(t => t.Use == "Fully specified name") ?? englishTranslations.Find(t => t.Use == "Preferred For Language"))?.Display ?? ""
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
                Console.WriteLine($"{fileName}: ");
                this.firstMessage = false;
            }

            if(original == null)
            {
                PrintWarningError(Printer.WARNING);
                Console.WriteLine($"Could not find {code}");
            }
            else if (original.ToLower() != nts.ToLower())
            {
                if (nts.Equals(""))
                {
                    PrintWarningError(Printer.WARNING);
                    Console.Write($"No translation available for code \"{code}\", please check manually");
                }
                else
                {
                    PrintWarningError(Printer.ERROR);
                    Console.Write($"{code}:\"{original}\" Should be:\"{nts}\" ");
                    if (ZiB)
                    {
                        Console.Write("According to the ZiB");
                    }
                }
                Console.WriteLine("");
            }
        }

        private void PrintWarningError(string level)
        {
            if (level == Printer.WARNING)
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.Write("\tWARNING: ");
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.Write("\tERROR: ");
            }

            Console.ResetColor();
        }
    }

}
