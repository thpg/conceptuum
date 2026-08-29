// Conceptuum visualizer: веб-интерфейс для базы понятий jnana3.
// Список понятий + поиск, клик — дерево зависимостей (род/виды) и связи.
//
// Запуск:  go run .            (порт :7100)
// DSN по умолчанию: root:123@tcp(127.0.0.1:3306)/jnana3 — переопределяется
// переменной окружения JNANA_DSN.
package main

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"

	_ "github.com/go-sql-driver/mysql"
)

var db *sql.DB
var relNames = map[string]string{} // kod -> long_name
var uniNames = map[int]string{}    // id -> nama

func dsn() string {
	if s := os.Getenv("JNANA_DSN"); s != "" {
		return s
	}
	return "root:123@tcp(127.0.0.1:3306)/jnana3?charset=utf8mb4&collation=utf8mb4_unicode_ci"
}

type Concept struct {
	ID   int    `json:"id"`
	Nama string `json:"nama"`
	Uni  int    `json:"uni"`
}

type Term struct {
	Term string `json:"term"`
	Lang string `json:"lang"`
}

type Rel struct {
	Kod      string   `json:"kod"`
	Name     string   `json:"name"`
	Dir      string   `json:"dir"` // "out" (это субъект) / "in" (это объект)
	Other    Concept  `json:"other"`
	Strength *int     `json:"strength,omitempty"`
}

type ConceptInfo struct {
	Concept
	Defin     string   `json:"defin"`
	UniName   string   `json:"uniName"`
	Processed bool     `json:"processed"`
	Parents   []Concept `json:"parents"`
	Children  []Concept `json:"children"`
	Rels      []Rel    `json:"rels"`
	Terms     []Term   `json:"terms"`
}

type TreeNode struct {
	ID         int         `json:"id"`
	Nama       string      `json:"nama"`
	Uni        int         `json:"uni"`
	ChildCount int         `json:"childCount"`
	Parents    []*TreeNode `json:"parents,omitempty"`
	Children   []*TreeNode `json:"children,omitempty"`
}

type TreeResp struct {
	Center ConceptInfo `json:"center"`
	Up     *TreeNode   `json:"up"`   // цепочка родов вверх
	Down   *TreeNode   `json:"down"` // дерево видов вниз
}

func main() {
	var err error
	db, err = sql.Open("mysql", dsn())
	if err != nil {
		log.Fatal(err)
	}
	if err = db.Ping(); err != nil {
		log.Fatal("нет соединения с БД: ", err)
	}
	loadDicts()

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/" {
			http.NotFound(w, r)
			return
		}
		http.ServeFile(w, r, "static/index.html")
	})
	http.HandleFunc("/api/search", handleSearch)
	http.HandleFunc("/api/concept", handleConcept)
	http.HandleFunc("/api/tree", handleTree)

	addr := ":7100"
	log.Printf("Conceptuum visualizer: http://localhost%s/", addr)
	log.Fatal(http.ListenAndServe(addr, nil))
}

func loadDicts() {
	rows, err := db.Query("SELECT kod, long_name FROM relevant")
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var k, n string
			rows.Scan(&k, &n)
			relNames[k] = n
		}
	}
	rows2, err := db.Query("SELECT id, nama FROM universum")
	if err == nil {
		defer rows2.Close()
		for rows2.Next() {
			var id int
			var n string
			rows2.Scan(&id, &n)
			uniNames[id] = n
		}
	}
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	json.NewEncoder(w).Encode(v)
}

// --- поиск: точное совпадение термина/имени, затем по подстроке ---
func handleSearch(w http.ResponseWriter, r *http.Request) {
	q := strings.TrimSpace(r.URL.Query().Get("q"))
	if q == "" {
		writeJSON(w, []Concept{})
		return
	}
	like := "%" + q + "%"
	rows, err := db.Query(`
		SELECT DISTINCT c.dharma, c.nama, c.universum_id,
		       CASE WHEN LOWER(c.nama)=LOWER(?) THEN 0
		            WHEN LOWER(t.term)=LOWER(?) THEN 1
		            WHEN LOWER(c.nama) LIKE LOWER(?) THEN 2 ELSE 3 END AS prio
		FROM concept c
		LEFT JOIN concept_term t ON t.concept_id = c.dharma
		WHERE LOWER(c.nama) LIKE LOWER(?) OR LOWER(t.term) LIKE LOWER(?)
		ORDER BY prio, c.universum_id, c.nama
		LIMIT 100`, q, q, q+"%", like, like)
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	defer rows.Close()
	out := []Concept{}
	seen := map[int]bool{}
	for rows.Next() {
		var c Concept
		var prio int
		if rows.Scan(&c.ID, &c.Nama, &c.Uni, &prio) == nil && !seen[c.ID] {
			seen[c.ID] = true
			out = append(out, c)
		}
	}
	writeJSON(w, out)
}

func scanConcepts(rows *sql.Rows) []Concept {
	defer rows.Close()
	out := []Concept{}
	for rows.Next() {
		var c Concept
		rows.Scan(&c.ID, &c.Nama, &c.Uni)
		out = append(out, c)
	}
	return out
}

func getConceptInfo(id int) (*ConceptInfo, error) {
	var ci ConceptInfo
	var defin sql.NullString
	var proc sql.NullInt64
	err := db.QueryRow("SELECT dharma, nama, universum_id, defin, processed FROM concept WHERE dharma=?", id).
		Scan(&ci.ID, &ci.Nama, &ci.Uni, &defin, &proc)
	if err != nil {
		return nil, err
	}
	ci.Defin = defin.String
	ci.Processed = proc.Int64 != 0
	ci.UniName = uniNames[ci.Uni]

	ci.Parents = scanConcepts(mustRows(`
		SELECT c.dharma, c.nama, c.universum_id FROM edge e
		JOIN concept c ON c.dharma=e.dh2
		WHERE e.dh1=? AND e.kod='14' AND e.status='ok' ORDER BY c.nama`, id))
	ci.Children = scanConcepts(mustRows(`
		SELECT c.dharma, c.nama, c.universum_id FROM edge e
		JOIN concept c ON c.dharma=e.dh1
		WHERE e.dh2=? AND e.kod='14' AND e.status='ok' ORDER BY c.nama`, id))

	rows := mustRows(`
		SELECT e.kod, e.dh1, e.dh2, e.strength,
		       c1.nama, c1.universum_id, c2.nama, c2.universum_id
		FROM edge e
		JOIN concept c1 ON c1.dharma=e.dh1
		JOIN concept c2 ON c2.dharma=e.dh2
		WHERE (e.dh1=? OR e.dh2=?) AND e.kod<>'14' AND e.status='ok'
		ORDER BY e.kod`, id, id)
	defer rows.Close()
	for rows.Next() {
		var r Rel
		var dh1, dh2 int
		var s sql.NullInt64
		var n1, n2 string
		var u1, u2 int
		rows.Scan(&r.Kod, &dh1, &dh2, &s, &n1, &u1, &n2, &u2)
		r.Name = relNames[r.Kod]
		if s.Valid {
			v := int(s.Int64)
			r.Strength = &v
		}
		if dh1 == id {
			r.Dir = "out"
			r.Other = Concept{dh2, n2, u2}
		} else {
			r.Dir = "in"
			r.Other = Concept{dh1, n1, u1}
		}
		ci.Rels = append(ci.Rels, r)
	}

	trows := mustRows(`SELECT term, lang FROM concept_term WHERE concept_id=? ORDER BY lang, term`, id)
	defer trows.Close()
	for trows.Next() {
		var t Term
		trows.Scan(&t.Term, &t.Lang)
		ci.Terms = append(ci.Terms, t)
	}
	return &ci, nil
}

func mustRows(q string, args ...any) *sql.Rows {
	rows, err := db.Query(q, args...)
	if err != nil {
		log.Println("query error:", err)
	}
	return rows
}

func handleConcept(w http.ResponseWriter, r *http.Request) {
	id, _ := strconv.Atoi(r.URL.Query().Get("id"))
	ci, err := getConceptInfo(id)
	if err != nil {
		http.Error(w, "not found", 404)
		return
	}
	writeJSON(w, ci)
}

// --- дерево ---
func nodeOf(id int) *TreeNode {
	var n TreeNode
	n.ID = id
	db.QueryRow("SELECT nama, universum_id FROM concept WHERE dharma=?", id).Scan(&n.Nama, &n.Uni)
	db.QueryRow(`SELECT COUNT(*) FROM edge WHERE dh2=? AND kod='14' AND status='ok'`, id).Scan(&n.ChildCount)
	return &n
}

func buildUp(id int, depth int, seen map[int]bool) *TreeNode {
	n := nodeOf(id)
	if depth <= 0 || seen[id] {
		return n
	}
	seen[id] = true
	rows := mustRows(`SELECT dh2 FROM edge WHERE dh1=? AND kod='14' AND status='ok'`, id)
	defer rows.Close()
	for rows.Next() {
		var p int
		rows.Scan(&p)
		n.Parents = append(n.Parents, buildUp(p, depth-1, seen))
	}
	return n
}

func buildDown(id int, depth int, seen map[int]bool) *TreeNode {
	n := nodeOf(id)
	if depth <= 0 || seen[id] {
		return n
	}
	seen[id] = true
	rows := mustRows(`SELECT dh1 FROM edge WHERE dh2=? AND kod='14' AND status='ok'
	                  ORDER BY (SELECT nama FROM concept WHERE dharma=dh1) LIMIT 200`, id)
	defer rows.Close()
	for rows.Next() {
		var c int
		rows.Scan(&c)
		n.Children = append(n.Children, buildDown(c, depth-1, seen))
	}
	return n
}

func handleTree(w http.ResponseWriter, r *http.Request) {
	id, _ := strconv.Atoi(r.URL.Query().Get("id"))
	depth, _ := strconv.Atoi(r.URL.Query().Get("depth"))
	if depth <= 0 || depth > 6 {
		depth = 3
	}
	ci, err := getConceptInfo(id)
	if err != nil {
		http.Error(w, "not found", 404)
		return
	}
	resp := TreeResp{
		Center: *ci,
		Up:     buildUp(id, 10, map[int]bool{}),
		Down:   buildDown(id, depth, map[int]bool{}),
	}
	writeJSON(w, resp)
}

