package main

import (
	"context"
	"fmt"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"time"
)

const maxEulerConcepts = 8
const maxEulerGenera = 8

type eulerEdge struct {
	ID   int    `json:"id"`
	From int    `json:"from"`
	To   int    `json:"to"`
	Code string `json:"code"`
}

type eulerPair struct {
	A        int         `json:"a"`
	B        int         `json:"b"`
	Kind     string      `json:"kind"` // inside means A is included in B
	Inferred bool        `json:"inferred"`
	Evidence []eulerEdge `json:"evidence"`
}

type eulerResponse struct {
	Basis         string        `json:"basis"`
	Catalog       *eulerCatalog `json:"catalog,omitempty"`
	Concepts      []Concept     `json:"concepts"`
	Pairs         []eulerPair   `json:"pairs"`
	Missing       []int         `json:"missing"`
	Context       int           `json:"context"`
	Limit         int           `json:"limit"`
	Automatic     []eulerGenus  `json:"automatic"`
	OmittedGenera int           `json:"omitted_genera"`
}

type eulerGenus struct {
	ID       int   `json:"id"`
	Children []int `json:"children"`
}

func parseEulerIDs(raw string) ([]int, error) {
	out := []int{}
	if strings.TrimSpace(raw) == "" {
		return out, nil
	}
	parts := strings.Split(raw, ",")
	if len(parts) > 32 {
		return nil, fmt.Errorf("select at most %d concepts", maxEulerConcepts)
	}
	seen := map[int]bool{}
	for _, part := range parts {
		id, err := strconv.Atoi(strings.TrimSpace(part))
		if err != nil || id <= 0 {
			return nil, fmt.Errorf("concept IDs must be positive integers")
		}
		if !seen[id] {
			out = append(out, id)
			seen[id] = true
		}
	}
	if len(out) > maxEulerConcepts {
		return nil, fmt.Errorf("select at most %d concepts", maxEulerConcepts)
	}
	return out, nil
}

// Reachability follows genus edges upwards and coextension in both directions.
// A visited set handles cycles without treating siblings as disjoint sets.
type eulerStep struct {
	previous int
	edge     eulerEdge
}

func eulerReach(start int, adjacency map[int][]eulerEdge) map[int]eulerStep {
	visited := map[int]eulerStep{start: {previous: start}}
	queue := []int{start}
	for cursor := 0; cursor < len(queue); cursor++ {
		from := queue[cursor]
		for _, edge := range adjacency[from] {
			to := edge.To
			if edge.Code == "30" && edge.To == from {
				to = edge.From
			}
			if _, exists := visited[to]; !exists {
				visited[to] = eulerStep{previous: from, edge: edge}
				queue = append(queue, to)
			}
		}
	}
	return visited
}

func eulerPath(reachable map[int]eulerStep, target int) []eulerEdge {
	path := []eulerEdge{}
	for step, ok := reachable[target]; ok && step.edge.ID != 0; step, ok = reachable[target] {
		path = append(path, step.edge)
		target = step.previous
	}
	for i, j := 0, len(path)-1; i < j; i, j = i+1, j-1 {
		path[i], path[j] = path[j], path[i]
	}
	return path
}

// Only accepted, positive edges from ONE discourse context reach this function.
// 61 (co-hyponyms) and 63 (opposition) do not establish disjoint extensions.
func deriveEulerPairs(concepts []Concept, edges []eulerEdge) []eulerPair {
	up, equal := map[int][]eulerEdge{}, map[int][]eulerEdge{}
	var overlaps, exclusions []eulerEdge
	for _, edge := range edges {
		switch edge.Code {
		case "14":
			up[edge.From] = append(up[edge.From], edge)
		case "30":
			up[edge.From] = append(up[edge.From], edge)
			up[edge.To] = append(up[edge.To], edge)
			equal[edge.From] = append(equal[edge.From], edge)
			equal[edge.To] = append(equal[edge.To], edge)
		case "40":
			overlaps = append(overlaps, edge)
		case "60", "64":
			exclusions = append(exclusions, edge)
		}
	}
	reach, equivalents := map[int]map[int]eulerStep{}, map[int]map[int]eulerStep{}
	for _, concept := range concepts {
		reach[concept.ID] = eulerReach(concept.ID, up)
		equivalents[concept.ID] = eulerReach(concept.ID, equal)
	}
	out := []eulerPair{}
	for i, first := range concepts {
		for _, second := range concepts[i+1:] {
			a, b := first.ID, second.ID
			pair := eulerPair{A: a, B: b, Kind: "unknown", Evidence: []eulerEdge{}}
			_, eq := equivalents[a][b]
			_, inside := reach[a][b]
			_, contains := reach[b][a]
			if eq {
				pair.Kind = "equal"
				pair.Evidence = eulerPath(equivalents[a], b)
			} else if inside && contains {
				pair.Kind = "conflict"
				pair.Evidence = append(eulerPath(reach[a], b), eulerPath(reach[b], a)...)
			} else if inside {
				pair.Kind = "inside"
				pair.Evidence = eulerPath(reach[a], b)
			} else if contains {
				pair.Kind = "contains"
				pair.Evidence = eulerPath(reach[b], a)
			}
			for _, relation := range []struct {
				edges []eulerEdge
				kind  string
				paths map[int]map[int]eulerStep
			}{{overlaps, "overlap", equivalents}, {exclusions, "disjoint", reach}} {
				for _, edge := range relation.edges {
					left, right := edge.From, edge.To
					_, matchA := relation.paths[a][left]
					_, matchB := relation.paths[b][right]
					if !matchA || !matchB {
						left, right = right, left
						_, matchA = relation.paths[a][left]
						_, matchB = relation.paths[b][right]
					}
					if !matchA || !matchB {
						continue
					}
					if pair.Kind != "unknown" && pair.Kind != relation.kind {
						pair.Kind = "conflict"
					} else {
						pair.Kind = relation.kind
					}
					pair.Evidence = append(pair.Evidence, eulerPath(relation.paths[a], left)...)
					pair.Evidence = append(pair.Evidence, edge)
					pair.Evidence = append(pair.Evidence, eulerPath(relation.paths[b], right)...)
					break
				}
			}
			pair.Inferred = len(pair.Evidence) > 1 && pair.Kind != "conflict"
			out = append(out, pair)
		}
	}
	return out
}

// Add direct shared genera, not arbitrary common ancestors. Equality aliases
// count as one species; a selected ancestor/descendant pair is not a sibling pair.
// Context and acceptance filtering happens before this pure graph operation.
func sharedEulerGenera(ids []int, edges []eulerEdge) []eulerGenus {
	up, equal := map[int][]eulerEdge{}, map[int][]eulerEdge{}
	for _, edge := range edges {
		if edge.Code == "14" {
			up[edge.From] = append(up[edge.From], edge)
		} else if edge.Code == "30" {
			for _, id := range []int{edge.From, edge.To} {
				up[id] = append(up[id], edge)
				equal[id] = append(equal[id], edge)
			}
		}
	}
	canonical := map[int]int{}
	canon := func(id int) int {
		if c, ok := canonical[id]; ok {
			return c
		}
		equivalents := eulerReach(id, equal)
		lowest := id
		for other := range equivalents {
			if other < lowest {
				lowest = other
			}
		}
		for other := range equivalents {
			canonical[other] = lowest
		}
		return lowest
	}
	reach := map[int]map[int]eulerStep{}
	ancestors := func(id int) map[int]eulerStep {
		if reach[id] == nil {
			reach[id] = eulerReach(id, up)
		}
		return reach[id]
	}
	selected := map[int]bool{}
	for _, id := range ids {
		selected[canon(id)] = true
	}
	children := map[int]map[int]bool{}
	for _, id := range ids {
		for equivalent := range eulerReach(id, equal) {
			for _, edge := range up[equivalent] {
				if edge.Code != "14" {
					continue
				}
				genus := canon(edge.To)
				if selected[genus] {
					continue
				}
				if _, cyclic := ancestors(genus)[id]; cyclic {
					continue
				}
				if children[genus] == nil {
					children[genus] = map[int]bool{}
				}
				children[genus][id] = true
			}
		}
	}
	candidates := []eulerGenus{}
	for genus, members := range children {
		group := eulerGenus{ID: genus, Children: []int{}}
		for _, id := range ids {
			if members[id] {
				group.Children = append(group.Children, id)
			}
		}
		siblings := false
		for i, a := range group.Children {
			for _, b := range group.Children[i+1:] {
				_, aInside := ancestors(a)[b]
				_, bInside := ancestors(b)[a]
				if !aInside && !bInside {
					siblings = true
				}
			}
		}
		if siblings {
			candidates = append(candidates, group)
		}
	}
	// Prefer a more specific shared genus when redundant direct edges also
	// point every one of its selected species at a broader genus.
	out := []eulerGenus{}
	for _, candidate := range candidates {
		redundant := false
		for _, other := range candidates {
			if other.ID == candidate.ID {
				continue
			}
			_, narrower := ancestors(other.ID)[candidate.ID]
			_, cyclic := ancestors(candidate.ID)[other.ID]
			if !narrower || cyclic {
				continue
			}
			covers := true
			for _, id := range candidate.Children {
				if !children[other.ID][id] {
					covers = false
				}
			}
			if covers {
				redundant = true
				break
			}
		}
		if !redundant {
			out = append(out, candidate)
		}
	}
	sort.Slice(out, func(i, j int) bool {
		if len(out[i].Children) != len(out[j].Children) {
			return len(out[i].Children) > len(out[j].Children)
		}
		return out[i].ID < out[j].ID
	})
	return out
}

func readEulerConcepts(ctx context.Context, ids []int, lang string) (map[int]Concept, error) {
	placeholders := strings.TrimSuffix(strings.Repeat("?,", len(ids)), ",")
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	rows, err := db.QueryContext(ctx, `SELECT dharma,nama,universum_id,COALESCE(processed,0) FROM concept WHERE dharma IN (`+placeholders+`)`, args...)
	if err != nil {
		return nil, err
	}
	byID := map[int]Concept{}
	for rows.Next() {
		var concept Concept
		if err := rows.Scan(&concept.ID, &concept.Nama, &concept.Uni, &concept.Processed); err != nil {
			rows.Close()
			return nil, err
		}
		byID[concept.ID] = concept
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	termArgs := append([]any{lang}, args...)
	rows, err = db.QueryContext(ctx, `SELECT concept_id,term FROM concept_term WHERE lang=? AND concept_id IN (`+placeholders+`) ORDER BY term`, termArgs...)
	if err != nil {
		return nil, err
	}
	terms := map[int][]string{}
	for rows.Next() {
		var id int
		var term string
		if err := rows.Scan(&id, &term); err != nil {
			rows.Close()
			return nil, err
		}
		terms[id] = append(terms[id], term)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	for id, concept := range byID {
		if name := pickDispTerm(lang, terms[id]); name != "" {
			concept.Nama = name
			byID[id] = concept
		}
	}
	return byID, nil
}

func readEuler(ctx context.Context, ids []int, universe int, lang, basis string) (*eulerResponse, error) {
	response := &eulerResponse{Basis: basis, Concepts: []Concept{}, Pairs: []eulerPair{}, Missing: []int{}, Automatic: []eulerGenus{}, Context: universe, Limit: maxEulerConcepts}
	if len(ids) == 0 {
		return response, nil
	}
	rows, err := db.QueryContext(ctx, `SELECT id,dh1,dh2,kod FROM edge WHERE universum_id=? AND status='ok' AND (strength IS NULL OR strength>0) AND kod IN ('14','30','40','60','64') ORDER BY id`, universe)
	if err != nil {
		return nil, err
	}
	edges := []eulerEdge{}
	for rows.Next() {
		var edge eulerEdge
		if err := rows.Scan(&edge.ID, &edge.From, &edge.To, &edge.Code); err != nil {
			rows.Close()
			return nil, err
		}
		edges = append(edges, edge)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	genera := sharedEulerGenera(ids, edges)
	if len(genera) > maxEulerGenera {
		response.OmittedGenera = len(genera) - maxEulerGenera
		genera = genera[:maxEulerGenera]
	}
	allIDs := append([]int{}, ids...)
	for _, genus := range genera {
		allIDs = append(allIDs, genus.ID)
	}
	byID, err := readEulerConcepts(ctx, allIDs, lang)
	if err != nil {
		return nil, err
	}
	for _, id := range ids {
		if concept, ok := byID[id]; ok {
			response.Concepts = append(response.Concepts, concept)
		} else {
			response.Missing = append(response.Missing, id)
		}
	}
	for _, genus := range genera {
		if concept, ok := byID[genus.ID]; ok {
			response.Automatic = append(response.Automatic, genus)
			response.Concepts = append(response.Concepts, concept)
		}
	}
	response.Pairs = deriveEulerPairs(response.Concepts, edges)
	if basis == "catalog" && len(response.Concepts) > 0 {
		if err := addEulerCatalog(ctx, response, edges, lang); err != nil {
			return nil, err
		}
	}
	return response, nil
}

func handleEuler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		w.Header().Set("Allow", http.MethodGet)
		http.Error(w, "use GET for Euler diagrams", http.StatusMethodNotAllowed)
		return
	}
	ids, err := parseEulerIDs(r.URL.Query().Get("ids"))
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	basis := r.URL.Query().Get("basis")
	if basis == "" {
		basis = "relations"
	}
	if basis != "relations" && basis != "catalog" {
		http.Error(w, "unknown Euler basis", http.StatusBadRequest)
		return
	}
	universe := 1
	if raw := r.URL.Query().Get("context"); raw != "" {
		universe, err = strconv.Atoi(raw)
		if err != nil || universe < 1 || universe > 5 {
			http.Error(w, "unknown relation context", http.StatusBadRequest)
			return
		}
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	response, err := readEuler(ctx, ids, universe, parseLang(r.URL.Query().Get("lang")), basis)
	if err != nil {
		http.Error(w, "Euler relationships are temporarily unavailable", http.StatusServiceUnavailable)
		return
	}
	writeJSON(w, response)
}
