package main

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestAlgebraProxyPreservesJSONAndStatus(t *testing.T) {
	body := `{"expression":"#25439 & #25446","context":1}`
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		got, _ := io.ReadAll(r.Body)
		if r.Method != "POST" || r.URL.Path != "/evaluate" || string(got) != body {
			t.Errorf("unexpected forwarded request: %s %s %s", r.Method, r.URL.Path, got)
		}
		if r.Header.Get("Authorization") != "" || r.Header.Get("Cookie") != "" {
			t.Error("forwarded private client headers")
		}
		w.WriteHeader(422)
		_, _ = w.Write([]byte(`{"error":{"message":"choose a sense"}}`))
	}))
	defer backend.Close()
	r := httptest.NewRequest("POST", "/api/algebra", strings.NewReader(body))
	r.Header.Set("Content-Type", "application/json; charset=utf-8")
	r.Header.Set("Authorization", "private-test-header")
	r.Header.Set("Cookie", "private-test-cookie")
	w := httptest.NewRecorder()
	newAlgebraHandler(backend.URL).ServeHTTP(w, r)
	if w.Code != 422 || !strings.Contains(w.Body.String(), "choose a sense") || w.Header().Get("Cache-Control") != "no-store" {
		t.Fatalf("unexpected result: %d %s", w.Code, w.Body.String())
	}
}

func TestQAProxyUsesFixedGeneratorPath(t *testing.T) {
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/generate" || r.Method != "POST" {
			t.Errorf("wrong route: %s %s", r.Method, r.URL.Path)
		}
		_, _ = w.Write([]byte(`{"schema":"conceptuum.qa.batch.v1","records":[]}`))
	}))
	defer backend.Close()
	r := httptest.NewRequest("POST", "/api/qa/generate", strings.NewReader(`{"count":20}`))
	r.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	newConceptProxy(backend.URL, "/generate").ServeHTTP(w, r)
	if w.Code != 200 || !strings.Contains(w.Body.String(), "conceptuum.qa.batch.v1") {
		t.Fatalf("unexpected response: %d %s", w.Code, w.Body.String())
	}
}

func TestAlgebraProxyRejectsInvalidInput(t *testing.T) {
	for _, tc := range []struct {
		method, contentType, body string
		status                    int
	}{
		{"GET", "application/json", "{}", 405},
		{"POST", "text/plain", "{}", 415},
		{"POST", "application/json", "broken", 400},
		{"POST", "application/json", strings.Repeat(" ", algebraBodyLimit+1), 413},
	} {
		r := httptest.NewRequest(tc.method, "/api/algebra", strings.NewReader(tc.body))
		r.Header.Set("Content-Type", tc.contentType)
		w := httptest.NewRecorder()
		newAlgebraHandler("http://127.0.0.1:1").ServeHTTP(w, r)
		if w.Code != tc.status {
			t.Errorf("got %d, want %d", w.Code, tc.status)
		}
	}
}

func TestAlgebraProxyRestrictsBackendToLoopback(t *testing.T) {
	for _, endpoint := range []string{"https://example.com", "http://example.com", "http://127.0.0.1/path", "http://user@localhost", "http://localhost?x=1", ":bad"} {
		r := httptest.NewRequest("POST", "/api/algebra", strings.NewReader("{}"))
		r.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		newAlgebraHandler(endpoint).ServeHTTP(w, r)
		if w.Code != 503 {
			t.Errorf("endpoint %s: got %d", endpoint, w.Code)
		}
	}
}

func TestAlgebraProxyRejectsBadBackendResponses(t *testing.T) {
	for _, tc := range []struct {
		status int
		body   string
	}{
		{302, `{}`}, {200, `<html>error</html>`}, {200, `{"text":"` + strings.Repeat("x", 2*1024*1024) + `"}`},
	} {
		backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Location", "https://example.com")
			w.WriteHeader(tc.status)
			_, _ = w.Write([]byte(tc.body))
		}))
		r := httptest.NewRequest("POST", "/api/algebra", strings.NewReader("{}"))
		r.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()
		newAlgebraHandler(backend.URL).ServeHTTP(w, r)
		backend.Close()
		if w.Code != 502 {
			t.Errorf("got %d, want 502", w.Code)
		}
	}
}

func TestAlgebraProxyUnavailable(t *testing.T) {
	backend := httptest.NewServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {}))
	endpoint := backend.URL
	backend.Close()
	r := httptest.NewRequest("POST", "/api/algebra", strings.NewReader("{}"))
	r.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	newAlgebraHandler(endpoint).ServeHTTP(w, r)
	if w.Code != 503 {
		t.Fatalf("got %d, want 503", w.Code)
	}
}
