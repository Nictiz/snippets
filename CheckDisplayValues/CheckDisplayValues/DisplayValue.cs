using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CheckDisplayValues
{
    public class DisplayValue
    {
        public string system;
        public string code;
        public string displayCurrent;
        public List<Translation> displayCorrect;

        /// <summary>
        /// A specific displayvalue containing all correct translations
        /// </summary>
        /// <param name="system">Corresponding system of the code (LOINC or SNOMED)</param>
        /// <param name="code">The code itself</param>
        /// <param name="displayCurrent">The current displayValue</param>
        /// <param name="displayCorrect"></param>
        public DisplayValue(string system, string code, string displayCurrent, List<Translation> displayCorrect)
        {
            this.system = system;
            this.code = code;
            this.displayCurrent = displayCurrent;
            this.displayCorrect = displayCorrect;
            //this.location = location;
        }

        public bool IsZiBValueSet()
        {
            return displayCorrect.Any(x => x.Use == "ZiB");
        }

        public List<Translation>? GetDutchDisplayValues()
        {
            List<Translation> dutchDisplayValues = new List<Translation>();
            foreach(Translation translation in displayCorrect)
            {
                if (translation.Language.Contains("nl"))
                {
                    dutchDisplayValues.Add(translation);
                }
            }

            if(dutchDisplayValues.Count > 0)
            {
                return dutchDisplayValues;
            }
            else
            {
                return null;
            }
        }

        public List<Translation>? GetEnglishDisplayValues()
        {
            List<Translation> englishDisplayValues = new List<Translation>();
            foreach (Translation translation in displayCorrect)
            {
                if (translation.Language.Contains("en"))
                {
                    englishDisplayValues.Add(translation);
                }
            }

            if (englishDisplayValues.Count > 0)
            {
                return englishDisplayValues;
            }
            else
            {
                return null;
            }
        }
    }
}
