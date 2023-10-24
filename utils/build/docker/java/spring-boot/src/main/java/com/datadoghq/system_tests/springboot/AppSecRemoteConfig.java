package com.datadoghq.system_tests.springboot;

import datadog.trace.api.DDTags;
import io.opentracing.Span;
import io.opentracing.Tracer;
import io.opentracing.util.GlobalTracer;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import javax.servlet.http.HttpServletRequest;

@RestController
public class AppSecRemoteConfig {

    @GetMapping(value = "/createextraservice")
    public String createextraservice(HttpServletRequest request) {
        final String serviceName = request.getParameter("serviceName");
        Tracer tracer = GlobalTracer.get();
        Span span = tracer.activeSpan();
        span.setTag(DDTags.SERVICE_NAME, serviceName);
        return "ok";
    }

}
