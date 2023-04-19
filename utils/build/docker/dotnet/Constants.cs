namespace weblog
{
    public static class Constants
    {
        public const string SqlConnectionString = @"Server=mssql-db;User Id=sa;Password=non-prod-password123;";
        public const string NpgSqlConnectionString = @"Server=postgres;User Id=system_tests_user;Database=system_tests;Port=5433;Password=system_tests;";
    }
}
