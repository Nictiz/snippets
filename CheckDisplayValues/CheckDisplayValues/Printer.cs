﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CheckDisplayValues
{
    public static class Printer
    {
        public static void PrintInconsistency(List<DisplayValue> displayValues)
        {
            foreach(DisplayValue displayValue in displayValues)
            {
                if (displayValue.IsZiBValueSet())
                {
                    PrintMessage(displayValue.displayCurrent, displayValue.displayCorrect.First(x => x.Use == "ZiB").Display, displayValue.code, true);
                }
                else
                {
                    List<Translation> dutchTranslations = displayValue.GetDutchDisplayValues();
                    List<Translation> englishTranslations = displayValue.GetDutchDisplayValues();

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
        private static void PrintMessage(string original, string nts, string code, bool ZiB = false)
        {
            if (original.ToLower() != nts.ToLower())
            {
                Console.Write($"        {code}:\"{original}\" Should be:\"{nts}\" ");
                if (ZiB)
                {
                    Console.Write("According to the ZiB");
                }

                if (nts.Equals(""))
                {
                    Console.Write("WARNING!: No translation available, please check manually");
                }
                Console.WriteLine("");
            }
        }
    }

}
