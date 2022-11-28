using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Hosting;

namespace weblog
{
    public class ShutdownEndpoint : ISystemTestEndpoint
    {
        public void Register(Microsoft.AspNetCore.Routing.IEndpointRouteBuilder routeBuilder)
        {
            routeBuilder.MapGet("/shutdown", async context =>
            {
                await context.Response.WriteAsync("Shutting down...\\n");
            });
        }
    }
}
