using System.Text.Json.Nodes;
using System.Net.Http.Headers;
using Hl7.Fhir.Serialization;
using Hl7.Fhir.Model;
using Microsoft.Extensions.Configuration;
using ExcelDataReader;

namespace CheckDisplayValues
{
    public class NTS
    {
        public int savedSNOMEDLookups = 0;
        public int totalSNOMEDLookups = 0;
        public bool _connected = false;

        private HttpClient? client;
        private Dictionary<string, string> LOINCList;
        private List<DisplayValue> _displayValues;
        
        public NTS()
        {
            _displayValues = new();

            Console.Write("Establishing connection to NTS: ");

            try
            {
                //setup Rest call
                string? dir = Directory.GetCurrentDirectory();
                string? parent = Directory.GetParent(dir ?? "C:/")?.Parent?.Parent?.FullName;
                IConfigurationRoot MyConfig = new ConfigurationBuilder().AddJsonFile($"{parent}/appsettings.json").Build();

                client = new HttpClient();
                client.BaseAddress = new Uri("https://terminologieserver.nl/");
                client.DefaultRequestHeaders.Accept.Clear();
                client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

                Dictionary<string, string> param = new Dictionary<string, string>();
                param.Add("grant_type", MyConfig.GetValue<string>("AppSettings:grant_type"));
                param.Add("client_id", MyConfig.GetValue<string>("AppSettings:client_id"));
                param.Add("username", MyConfig.GetValue<string>("AppSettings:username"));
                param.Add("password", MyConfig.GetValue<string>("AppSettings:password"));


                HttpResponseMessage response = client.PostAsync("auth/realms/nictiz/protocol/openid-connect/token", new FormUrlEncodedContent(param)).Result;
                Console.WriteLine(response.StatusCode);
                if(response.StatusCode == System.Net.HttpStatusCode.OK)
                {
                    _connected = true;

                    var responseResult = response.Content.ReadAsStringAsync().Result;
                    var parsedResponse = JsonObject.Parse(responseResult);
                    var bearer = parsedResponse?["access_token"];

                    client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", bearer.ToString());
                }
                else
                {
                    throw new HttpRequestException();
                }

            }
            catch (Exception ex) 
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("ERROR: Failed to establish connection, continuing without NTS");
                Console.ResetColor();
                Console.WriteLine("");
                _connected = false;
            }
            

            //Read LOINC codes from .xlsx file
            LOINCList = new();

            System.Text.Encoding.RegisterProvider(System.Text.CodePagesEncodingProvider.Instance);
            using (var stream = File.Open("..\\..\\..\\LOINC\\LOINC-nlnames-2.73-patch.xlsx", FileMode.Open, FileAccess.Read))
            {
                using (var reader = ExcelReaderFactory.CreateReader(stream))
                {
                    do
                    {
                        while (reader.Read()) //Each ROW
                        {
                            string? code = null;
                            string? translation = null;

                            code = reader.GetValue(0).ToString();
                            translation = reader.GetValue(1).ToString();
                            LOINCList.Add(code ?? "9999-9", translation ?? "");
                        }
                    } while (reader.NextResult()); //Move to NEXT SHEET
                }
            }

        }

        public List<Translation> GetDisplayListValue(string code, string system)
        {
            if (system == "http://snomed.info/sct")
                totalSNOMEDLookups++;

            // By checking if we allready searched for this specific code, we don't have to do the entire lookup again.
            DisplayValue? displayValue = _displayValues.FirstOrDefault(x => x.code == code);
            if(displayValue != null)
            {
                if(system == "http://snomed.info/sct")
                    savedSNOMEDLookups++;

                return displayValue.displayCorrect.ConvertAll(Translation => Translation.DeepCopy());
            }
            else
            {
                List<Translation> translations = new List<Translation>();
                if (system == "http://snomed.info/sct" && _connected)
                {
                    HttpResponseMessage response = client.GetAsync($"fhir/CodeSystem/$lookup?system={system}&code={code}").Result;

                    var parser = new FhirJsonParser();
                    Parameters result = parser.Parse<Parameters>(response.Content.ReadAsStringAsync().Result);

                    List<Parameters.ParameterComponent> components = result.Parameter.FindAll(c => c.Name == "designation");

                    foreach (Parameters.ParameterComponent display in components)
                    {
                        string? language = display.Part.Find(l => l.Name == "language")?.Value.ToString();
                        Coding? use = display.Part.Find(l => l.Name == "use")?.Value as Coding;
                        string? value = display.Part.Find(l => l.Name == "value")?.Value.ToString();

                        translations.Add(new Translation()
                        {
                            Language = language,
                            Use = use?.Display ?? use?.Code,
                            Display = value
                        });

                    }
                }
                else if (system == "http://loinc.org")
                {
                    if (LOINCList.ContainsKey(code))
                    {
                        translations.Add(new Translation()
                        {
                            Language = "nl",
                            Use = "Preferred For Language",
                            Display = LOINCList[code]
                        });
                    }
                }

                // Adding the translations to our local displayValue storage, to save time if the code is used again.
                _displayValues.Add(new DisplayValue(system, code, "", translations.ConvertAll(Translation => Translation.DeepCopy()))); ;
                return translations;
            }
        }
    }
}
