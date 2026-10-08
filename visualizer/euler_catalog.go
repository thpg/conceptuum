package main

import (
	"context"
	"sort"
)

// Catalog sets contain concept records, not real-world instances. A root and
// everything reaching it through accepted 14/30 links belong to its set.
// The finite universe is the union of the displayed sets, including auto genera.
type eulerCatalog struct {
	UniverseCount int                  `json:"universe_count"`
	Sets          []eulerCatalogSet    `json:"sets"`
	Regions       []eulerCatalogRegion `json:"regions"`
	SampleLimit   int                  `json:"sample_limit"`
}
type eulerCatalogSet struct {
	ID    int `json:"id"`
	Count int `json:"count"`
}
type eulerCatalogRegion struct {
	Mask    int                  `json:"mask"`
	Count   int                  `json:"count"`
	Samples []eulerCatalogMember `json:"samples"`
}
type eulerCatalogMember struct {
	Concept
	Paths []eulerMembershipPath `json:"paths"`
}
type eulerMembershipPath struct {
	Set   int         `json:"set"`
	Edges []eulerEdge `json:"edges"`
}

func catalogReach(root int, down map[int][]eulerEdge, valid map[int]bool) map[int]eulerStep {
	seen := map[int]eulerStep{}
	if !valid[root] {
		return seen
	}
	seen[root] = eulerStep{previous: root}
	queue := []int{root}
	for cursor := 0; cursor < len(queue); cursor++ {
		from := queue[cursor]
		for _, edge := range down[from] {
			to := edge.From
			if edge.Code == "30" && to == from {
				to = edge.To
			}
			if !valid[to] {
				continue
			}
			if _, ok := seen[to]; !ok {
				seen[to] = eulerStep{previous: from, edge: edge}
				queue = append(queue, to)
			}
		}
	}
	return seen
}

func deriveEulerCatalog(concepts []Concept, edges []eulerEdge, valid map[int]bool) (*eulerCatalog, []eulerPair) {
	down := map[int][]eulerEdge{}
	for _, edge := range edges {
		if edge.Code == "14" || edge.Code == "30" {
			down[edge.To] = append(down[edge.To], edge)
		}
		if edge.Code == "30" {
			down[edge.From] = append(down[edge.From], edge)
		}
	}
	catalog := &eulerCatalog{Sets: []eulerCatalogSet{}, Regions: []eulerCatalogRegion{}, SampleLimit: 6}
	membership := map[int]int{}
	reach := make([]map[int]eulerStep, len(concepts))
	for i, c := range concepts {
		reach[i] = catalogReach(c.ID, down, valid)
		catalog.Sets = append(catalog.Sets, eulerCatalogSet{ID: c.ID, Count: len(reach[i])})
		for id := range reach[i] {
			membership[id] |= 1 << i
		}
	}
	catalog.UniverseCount = len(membership)
	regions := map[int][]int{}
	for id, mask := range membership {
		regions[mask] = append(regions[mask], id)
	}
	masks := []int{}
	for mask := range regions {
		masks = append(masks, mask)
	}
	sort.Ints(masks)
	for _, mask := range masks {
		ids := regions[mask]
		sort.Ints(ids)
		region := eulerCatalogRegion{Mask: mask, Count: len(ids), Samples: []eulerCatalogMember{}}
		if len(ids) > catalog.SampleLimit {
			ids = ids[:catalog.SampleLimit]
		}
		for _, id := range ids {
			member := eulerCatalogMember{Concept: Concept{ID: id}, Paths: []eulerMembershipPath{}}
			for i, c := range concepts {
				if mask&(1<<i) == 0 {
					continue
				}
				path := eulerPath(reach[i], id)
				// Return the witness from the member upwards, preserving real edge IDs.
				for l, r := 0, len(path)-1; l < r; l, r = l+1, r-1 {
					path[l], path[r] = path[r], path[l]
				}
				member.Paths = append(member.Paths, eulerMembershipPath{Set: c.ID, Edges: path})
			}
			region.Samples = append(region.Samples, member)
		}
		catalog.Regions = append(catalog.Regions, region)
	}
	pairs := []eulerPair{}
	for i, a := range concepts {
		for j := i + 1; j < len(concepts); j++ {
			common := 0
			for id := range reach[i] {
				if _, ok := reach[j][id]; ok {
					common++
				}
			}
			kind := "overlap"
			switch {
			case common == 0:
				kind = "disjoint"
			case common == len(reach[i]) && common == len(reach[j]):
				kind = "equal"
			case common == len(reach[i]):
				kind = "inside"
			case common == len(reach[j]):
				kind = "contains"
			}
			pairs = append(pairs, eulerPair{A: a.ID, B: concepts[j].ID, Kind: kind, Inferred: true, Evidence: []eulerEdge{}})
		}
	}
	return catalog, pairs
}

func addEulerCatalog(ctx context.Context, response *eulerResponse, edges []eulerEdge, lang string) error {
	// Check actual concept IDs so dangling edges never create phantom members.
	rows, err := db.QueryContext(ctx, `SELECT dharma FROM concept`)
	if err != nil {
		return err
	}
	valid := map[int]bool{}
	for rows.Next() {
		var id int
		if err := rows.Scan(&id); err != nil {
			rows.Close()
			return err
		}
		valid[id] = true
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	if err = ctx.Err(); err != nil {
		return err
	}
	response.Catalog, response.Pairs = deriveEulerCatalog(response.Concepts, edges, valid)
	ids := []int{}
	seen := map[int]bool{}
	for _, region := range response.Catalog.Regions {
		for _, sample := range region.Samples {
			if !seen[sample.ID] {
				ids = append(ids, sample.ID)
				seen[sample.ID] = true
			}
		}
	}
	if len(ids) == 0 {
		return nil
	}
	names, err := readEulerConcepts(ctx, ids, lang)
	if err != nil {
		return err
	}
	for i := range response.Catalog.Regions {
		for j := range response.Catalog.Regions[i].Samples {
			member := &response.Catalog.Regions[i].Samples[j]
			if c, ok := names[member.ID]; ok {
				member.Concept = c
			}
		}
	}
	return nil
}
