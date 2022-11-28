using System;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Routing;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;

namespace weblog
{
    [ApiController]
    [Route("shutdown")]
    public class ShutdownController : Controller
    {
        private IHostApplicationLifetime HostApplicationLifetime { get; set; }

        public ShutdownController(IHostApplicationLifetime appLifetime)
        {
            HostApplicationLifetime = appLifetime;
        }

        [HttpPost]
        public async Task ShutdownSite()
        {
            HostApplicationLifetime.StopApplication();
        }

    }
}
