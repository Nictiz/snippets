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
        HttpClient client;
        Dictionary<string, string> LOINCList;

        public NTS()
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
            var responseResult = response.Content.ReadAsStringAsync().Result;
            var parsedResponse = JsonObject.Parse(responseResult);
            var bearer = parsedResponse?["access_token"];

            client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", bearer.ToString());

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
            List<Translation> translations = new List<Translation>();
            if (system == "http://snomed.info/sct")
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
            }else if(system == "http://loinc.org") 
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
            return translations;
        }
    }
}
