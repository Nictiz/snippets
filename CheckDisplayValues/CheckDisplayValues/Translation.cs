using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CheckDisplayValues
{
    public class Translation
    {
        public string Language { get; set; }
        public string? Use { get; set; }
        public string? Display { get; set; }

        public Translation DeepCopy()
        {
            return new Translation()
            {
                Language = Language,
                Use = Use,
                Display = Display
            };
        }
    }
}
