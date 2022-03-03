package main

import (
	"net/http"

	"gopkg.in/DataDog/dd-trace-go.v1/appsec"
	muxtrace "gopkg.in/DataDog/dd-trace-go.v1/contrib/gorilla/mux"
	"gopkg.in/DataDog/dd-trace-go.v1/ddtrace/tracer"
)

func main() {
	tracer.Start()
	defer tracer.Stop()

	mux := muxtrace.NewRouter()

	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	mux.HandleFunc("/waf", func(w http.ResponseWriter, r *http.Request) {
		body, err := parseBody(r)
		if err == nil {
			appsec.MonitorParsedHTTPBody(r.Context(), body)
		}
		w.Write([]byte("Hello, WAF!\n"))
	})

	mux.HandleFunc("/waf/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("Hello, WAF!\n"))
	})

	mux.HandleFunc("/sample_rate_route/:i", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("OK"))
	})

	mux.HandleFunc("/params/{value}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("OK"))
	})

	mux.HandleFunc("/headers/", func(w http.ResponseWriter, r *http.Request) {
		//Data used for header content is irrelevant here, only header presence is checked
		w.Header().Set("content-type", "text/plain")
		w.Header().Set("content-length", "42")
		w.Header().Set("content-language", "en-US")
		w.Write([]byte("Hello, headers!"))
	})

	initDatadog()
	http.ListenAndServe(":7777", mux)
}
