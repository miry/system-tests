
using System;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Npgsql;

namespace weblog
{
    public class DbmEndpoint : ISystemTestEndpoint
    {
        public void Register(Microsoft.AspNetCore.Routing.IEndpointRouteBuilder routeBuilder)
        {
            routeBuilder.MapGet("/dbm", async context =>
            {
                var queryString = "SELECT version()";
                var integration = context.Request.Query["integration"];

                if (integration == "npgsql") 
                {
                    var con = new NpgsqlConnection(Constants.NpgSqlConnectionString);
                    con.Open();
                    
                    using var cmd = new NpgsqlCommand();
                    cmd.Connection = con;

                    cmd.CommandText = $"DROP TABLE IF EXISTS teachers";
                    await cmd.ExecuteNonQueryAsync();

                    // NpgsqlConnection connection = new NpgsqlConnection(Constants.NpgSqlConnectionString);
                    // connection.Open();

                    // NpgsqlCommand command = new NpgsqlCommand(queryString, conn);
                    // command.ExecuteScalar();
                    // conn.Close();

                    await context.Response.WriteAsync("NpgSql query executed.");
                } 
            });
        }
    }
}
