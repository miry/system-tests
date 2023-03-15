package com.datadoghq.resteasy;


import com.datadoghq.system_tests.springboot.iast.utils.CmdExamples;
import com.datadoghq.system_tests.springboot.iast.utils.CryptoExamples;
import com.datadoghq.system_tests.springboot.iast.utils.LDAPExamples;
import com.datadoghq.system_tests.springboot.iast.utils.PathExamples;
import com.datadoghq.system_tests.springboot.iast.utils.SqlExamples;
import com.datadoghq.system_tests.springboot.iast.utils.TestBean;
import io.opentracing.Span;
import io.opentracing.util.GlobalTracer;

import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Collections;
import javax.crypto.BadPaddingException;
import javax.crypto.IllegalBlockSizeException;
import javax.crypto.NoSuchPaddingException;
import javax.naming.NamingException;
import javax.ws.rs.*;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.Cookie;
import javax.ws.rs.core.HttpHeaders;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.MultivaluedMap;
import javax.ws.rs.core.PathSegment;
import javax.ws.rs.core.Response;
import javax.xml.bind.annotation.XmlAttribute;
import javax.xml.bind.annotation.XmlRootElement;
import javax.xml.bind.annotation.XmlValue;

import java.util.HashMap;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Map;
import java.util.List;
import org.h2.engine.User;
import org.jboss.resteasy.annotations.Body;
import org.jboss.resteasy.plugins.server.netty.NettyHttpRequest;

@Path("/")
@Produces(MediaType.TEXT_PLAIN)
public class MyResource {
    String superSecretAccessKey = "insecure";


    @GET
    public String hello() {
        var tracer = GlobalTracer.get();
        Span span = tracer.buildSpan("test-span").start();
        span.setTag("test-tag", "my value");
        try {
            return "Hello World!";
        } finally {
            span.finish();
        }
    }

    @GET
    @Path("/headers")
    public Response headers() {
        return Response.status(200)
                .header("content-type", "text/plain")
                .header("content-language", "en-US")
                .entity("012345678901234567890123456789012345678901").build();
    }

    @GET
    @Path("/params/{params: .*}")
    public String waf(@PathParam("params") List<PathSegment> params) {
        return params.toString();
    }

    @POST
    @Path("/waf")
    @Consumes(MediaType.APPLICATION_FORM_URLENCODED)
    public String postWafUrlencoded(MultivaluedMap<String, String> form) {
        return form.toString();
    }

    @POST
    @Path("/waf")
    @Consumes(MediaType.APPLICATION_JSON)
    public String postWafJson(Object node) {
        return node.toString();
    }

    @POST
    @Path("/waf")
    @Consumes(MediaType.APPLICATION_XML)
    public String postWafXml(XmlObject object) {
        return object.toString();
    }

    @GET
    @Path("/status")
    public Response status(@QueryParam("code") Integer code) {
        return Response.status(code).build();
    }

    private static final Map<String, String> METADATA = createMetadata();
    private static final Map<String, String> createMetadata() {
        HashMap<String, String> h = new HashMap<>();
        h.put("metadata0", "value0");
        h.put("metadata1", "value1");
        return h;
    }

    @GET
    @Path("/user_login_success_event")
    public String userLoginSuccess(@DefaultValue("system_tests_user") @QueryParam("event_user_id") String userId) {
        datadog.trace.api.GlobalTracer.getEventTracker()
                .trackLoginSuccessEvent(userId, METADATA);

        return "ok";
    }

    @GET
    @Path("/user_login_failure_event")
    public String userLoginFailure(@DefaultValue("system_tests_user") @QueryParam("event_user_id") String userId,
                                   @DefaultValue("true") @QueryParam("event_user_exists") boolean eventUserExists) {
        datadog.trace.api.GlobalTracer.getEventTracker()
                .trackLoginFailureEvent(userId, eventUserExists, METADATA);

        return "ok";
    }

    @GET
    @Path("/custom_event")
    public String customEvent(@DefaultValue("system_tests_event") @QueryParam("event_name") String eventName) {
        datadog.trace.api.GlobalTracer.getEventTracker()
                .trackCustomEvent(eventName, METADATA);

        return "ok";
    }

    @XmlRootElement(name = "string")
    public static class XmlObject {
        @XmlValue
        public String value;

        @XmlAttribute
        public String attack;

        @Override
        public String toString() {
            final StringBuilder sb = new StringBuilder("StringElement{");
            sb.append("value='").append(value).append('\'');
            sb.append(", attack='").append(attack).append('\'');
            sb.append('}');
            return sb.toString();
        }
    }

    @GET
    @Path("/make_distant_call")
    public DistantCallResponse make_distant_call(@QueryParam("url") String url) throws Exception {
        URL urlObject = new URL(url);

        HttpURLConnection con = (HttpURLConnection) urlObject.openConnection();
        con.setRequestMethod("GET");

        // Save request headers
        HashMap<String, String> request_headers = new HashMap<String, String>();
        for (Map.Entry<String, List<String>> header: con.getRequestProperties().entrySet()) {
            if (header.getKey() == null) {
                continue;
            }

            request_headers.put(header.getKey(), header.getValue().get(0));
        }

        // Save response headers and status code
        int status_code = con.getResponseCode();
        HashMap<String, String> response_headers = new HashMap<String, String>();
        for (Map.Entry<String, List<String>> header: con.getHeaderFields().entrySet()) {
            if (header.getKey() == null) {
                continue;
            }

            response_headers.put(header.getKey(), header.getValue().get(0));
        }

        DistantCallResponse result = new DistantCallResponse();
        result.url = url;
        result.status_code = status_code;
        result.request_headers = request_headers;
        result.response_headers = response_headers;

        return result;
    }

    public static final class DistantCallResponse {
        public String url;
        public int status_code;
        public HashMap<String, String> request_headers;
        public HashMap<String, String> response_headers;
    }

    @GET
    @Path("/iast/insecure_hashing/deduplicate")
    public String removeDuplicates() throws NoSuchAlgorithmException {
        return CryptoExamples.getSingleton().removeDuplicates(superSecretAccessKey);
    }

    @GET
    @Path("/iast/insecure_hashing/multiple_hash")
    public String multipleInsecureHash() throws NoSuchAlgorithmException {
        return CryptoExamples.getSingleton().multipleInsecureHash(superSecretAccessKey);
    }

    @GET
    @Path("/iast/insecure_hashing/test_secure_algorithm")
    public String secureHashing() throws NoSuchAlgorithmException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        return CryptoExamples.getSingleton().secureHashing(superSecretAccessKey);
    }

    @GET
    @Path("/iast/insecure_hashing/test_md5_algorithm")
    public String insecureMd5Hashing() throws NoSuchAlgorithmException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        return CryptoExamples.getSingleton().insecureMd5Hashing(superSecretAccessKey);
    }


    @GET
    @Path("/iast/insecure_cipher/test_secure_algorithm")
    public String secureCipher() throws NoSuchAlgorithmException, NoSuchPaddingException,
        IllegalBlockSizeException, BadPaddingException, InvalidKeyException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        return CryptoExamples.getSingleton().secureCipher(superSecretAccessKey);
    }

    @GET
    @Path("/iast/insecure_cipher/test_insecure_algorithm")
    public String insecureCipher() throws NoSuchAlgorithmException, NoSuchPaddingException,
        IllegalBlockSizeException, BadPaddingException, InvalidKeyException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        return CryptoExamples.getSingleton().insecureCipher(superSecretAccessKey);
    }

    @POST
    @Path("/iast/sqli/test_insecure")
    public Object insecureSql(@FormParam("username") String username, @FormParam("password") String password) throws SQLException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        return SqlExamples.insecureSql(username, password);
    }

    @POST
    @Path("/iast/sqli/test_secure")
    public Object secureSql(@FormParam("username") String username, @FormParam("password") String password) throws SQLException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        return SqlExamples.secureSql(username, password);
    }

    @POST
    @Path("/iast/cmdi/test_insecure")
    public String insecureCmd(@FormParam("cmd") final String cmd) {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        return new CmdExamples().insecureCmd(cmd);
    }

    @POST
    @Path("/iast/ldapi/test_insecure")
    public String insecureLDAP(@FormParam("username") final String username, @FormParam("password") final String password) throws NamingException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        return  new LDAPExamples().injection(username, password);
    }

    @POST
    @Path("/iast/ldapi/test_secure")
    public String secureLDAP() throws NamingException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        return new LDAPExamples().secure();
    }

    @POST
    @Path("/iast/path_traversal/test_insecure")
    public String insecurePathTraversal(@FormParam("path") final String path) {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        return new PathExamples().insecurePathTraversal(path);
    }

    @POST
    @Path("/iast/source/parameter/test")
    public String sourceParameter(@FormParam("source") final String source) throws SQLException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        try (final Connection con = SqlExamples.initDBAndGetConnection()) {
            final Statement statement = con.createStatement();
            final String sql = "SELECT * FROM USERS WHERE USERNAME = '" + source + "' AND PASSWORD = '" + source + "'";
            statement.executeQuery(sql);
        }
        return String.format("Request Parameters => source: %s", source);
    }

    @GET
    @Path("/iast/source/header/test")
    public String sourceHeaders(@HeaderParam("random-key") String header) throws SQLException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        try (final Connection con = SqlExamples.initDBAndGetConnection()) {
            final Statement statement = con.createStatement();
            final String sql = "SELECT * FROM USERS WHERE USERNAME = '" + header + "' AND PASSWORD = '" + header + "'";
            statement.executeQuery(sql);
        }
        return String.format("Request Headers => %s", header);
    }

    @GET
    @Path("/iast/source/cookievalue/test")
    public String sourceCookieValue(@CookieParam("cookie-source-name") final String value) throws SQLException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        try (final Connection con = SqlExamples.initDBAndGetConnection()) {
            final Statement statement = con.createStatement();
            final String sql = "SELECT * FROM USERS WHERE USERNAME = '" + value + "' AND PASSWORD = '" + value + "'";
            statement.executeQuery(sql);
        }
        return String.format("Request Cookies => %s", value);
    }

    @GET
    @Path("/iast/source/cookiename/test")
    public String sourceCookieName(@Context final HttpHeaders headers) throws SQLException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        Map<String, Cookie> cookies = headers.getCookies();
        for (Cookie cookie : cookies.values()) {
            String name = cookie.getName();
            try (final Connection con = SqlExamples.initDBAndGetConnection()) {
                final Statement statement = con.createStatement();
                final String sql = "SELECT * FROM USERS WHERE USERNAME = '" + name + "' AND PASSWORD = '" + name + "'";
                statement.executeQuery(sql);
            }
            break;
        }
        return String.format("Request Cookies => %s", cookies);
    }

    @POST
    @Path("/iast/source/body/test")
    public String sourceBody(TestBean testBean) throws SQLException {
        final Span span = GlobalTracer.get().activeSpan();
        if (span != null) {
            span.setTag("appsec.event", true);
        }
        System.out.println("Inside body test testbean: " + testBean);
        String name = testBean.getName();
        String value = testBean.getValue();
        try (final Connection con = SqlExamples.initDBAndGetConnection()) {
            final Statement statement = con.createStatement();
            final String sql = "SELECT * FROM USERS WHERE USERNAME = '" + name + "' AND PASSWORD = '" + value + "'";
            statement.executeQuery(sql);
        }
        return String.format("@RequestBody to Test bean -> name: %s, value:%", name, value);
    }

}
