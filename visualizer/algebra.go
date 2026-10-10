package main

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"mime"
	"net/http"
	"net/url"
	"os"
	"time"
)

const algebraBodyLimit = 96 * 1024

func algebraError(w http.ResponseWriter, status int, message string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]any{"error": map[string]string{"message": message}})
}

func newAlgebraHandler(endpoint string) http.Handler {
	return newConceptProxy(endpoint, "/evaluate")
}

func newConceptProxy(endpoint, path string) http.Handler {
	base, err := url.Parse(endpoint)
	valid := err == nil && base.Scheme == "http" && base.User == nil && base.RawQuery == "" && base.Fragment == "" && (base.Path == "" || base.Path == "/")
	valid = valid && (path == "/evaluate" || path == "/generate")
	if valid {
		valid = base.Hostname() == "127.0.0.1" || base.Hostname() == "localhost" || base.Hostname() == "::1"
	}
	client := &http.Client{Timeout: 20 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			w.Header().Set("Allow", "POST")
			algebraError(w, http.StatusMethodNotAllowed, "Use POST with a JSON expression")
			return
		}
		if !valid {
			algebraError(w, http.StatusServiceUnavailable, "Concept algebra is not configured")
			return
		}
		mediaType, _, parseErr := mime.ParseMediaType(r.Header.Get("Content-Type"))
		if parseErr != nil || mediaType != "application/json" {
			algebraError(w, http.StatusUnsupportedMediaType, "Use application/json")
			return
		}
		body, readErr := io.ReadAll(http.MaxBytesReader(w, r.Body, algebraBodyLimit))
		if readErr != nil {
			algebraError(w, http.StatusRequestEntityTooLarge, "Request exceeds the body limit")
			return
		}
		if !json.Valid(body) {
			algebraError(w, http.StatusBadRequest, "Request body must be valid JSON")
			return
		}
		ctx, cancel := context.WithTimeout(r.Context(), 20*time.Second)
		defer cancel()
		target := *base
		target.Path = path
		request, requestErr := http.NewRequestWithContext(ctx, http.MethodPost, target.String(), bytes.NewReader(body))
		if requestErr != nil {
			algebraError(w, http.StatusServiceUnavailable, "Concept algebra is not configured")
			return
		}
		request.Header.Set("Content-Type", "application/json")
		response, requestErr := client.Do(request)
		if requestErr != nil {
			algebraError(w, http.StatusServiceUnavailable, "Concept algebra is temporarily unavailable. Try again shortly.")
			return
		}
		defer response.Body.Close()
		payload, readErr := io.ReadAll(io.LimitReader(response.Body, 2*1024*1024+1))
		if readErr != nil || len(payload) > 2*1024*1024 || !json.Valid(payload) || response.StatusCode >= 300 && response.StatusCode < 400 {
			algebraError(w, http.StatusBadGateway, "Concept algebra returned an incomplete response")
			return
		}
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.WriteHeader(response.StatusCode)
		_, _ = w.Write(payload)
	})
}

func algebraHandler() http.Handler {
	return conceptProxy("/evaluate")
}

func conceptProxy(path string) http.Handler {
	endpoint := os.Getenv("CONCEPTUUM_ALGEBRA_URL")
	if endpoint == "" {
		endpoint = "http://127.0.0.1:7101"
	}
	return newConceptProxy(endpoint, path)
}
