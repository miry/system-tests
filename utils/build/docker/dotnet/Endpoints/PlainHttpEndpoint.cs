using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;

namespace weblog
{
    public class PlainHttpEndpoint : ISystemTestEndpoint
    {
        public void Register(Microsoft.AspNetCore.Routing.IEndpointRouteBuilder routeBuilder)
        {
            routeBuilder.MapGet("/", async context =>
            {
                overrideAPIKey(context.Request);

                // Process response
                await context.Response.WriteAsync("Hello world!\\n");
            });
        }

        // Add the custom tag that will override the "DD-Api-Key" inside `asm-signals-generator`
        public void overrideAPIKey(HttpRequest request) {
            request.Headers.TryGetValue("X-Override-API-Key", out var headerValue);
            Helper.AddCustomSpanTags("X-Override-API-Key:" + headerValue);
        }
    }
}
