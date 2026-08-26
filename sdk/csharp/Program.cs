using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Threading.Tasks;

namespace BedrockGatewayClient
{
    class Program
    {
        static async Task Main(string[] args)
        {
            var baseUrl = Environment.GetEnvironmentVariable("BEDROCK_GATEWAY_URL") ?? "http://localhost:8000/v1/";
            var apiKey = Environment.GetEnvironmentVariable("BEDROCK_API_KEY") ?? "sk-live-sample-key-123";

            using var httpClient = new HttpClient { BaseAddress = new Uri(baseUrl) };
            httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");

            var payload = new
            {
                model = "anthropic.claude-3-5-sonnet-20241022-v2:0",
                messages = new[]
                {
                    new { role = "user", content = "Explain .NET 8 memory management and garbage collection." }
                },
                stream = false
            };

            Console.WriteLine("Invoking AWS Bedrock via Gateway...");
            var response = await httpClient.PostAsJsonAsync("chat/completions", payload);

            if (response.IsSuccessStatusCode)
            {
                var jsonDoc = await response.Content.ReadFromJsonAsync<JsonDocument>();
                var content = jsonDoc.RootElement
                    .GetProperty("choices")[0]
                    .GetProperty("message")
                    .GetProperty("content")
                    .GetString();

                Console.WriteLine($"\n[Response]:\n{content}");
            }
            else
            {
                var errorText = await response.Content.ReadAsStringAsync();
                Console.WriteLine($"Error ({response.StatusCode}): {errorText}");
            }
        }
    }
}
