package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/olekukonko/tablewriter"
	"github.com/tidwall/gjson"
)

var (
	host   string
	port   string
	client *http.Client
)

func init() {
	host = os.Getenv("ELASTICSEARCH_HOST")
	if host == "" {
		host = "localhost"
	}

	port = os.Getenv("ELASTICSEARCH_PORT")
	if port == "" {
		port = "9200"
	}

	client = &http.Client{
		Timeout: 30 * time.Second,
	}
}

func main() {
	fmt.Printf("Connected to Elasticsearch at %s:%s\n", host, port)
	fmt.Println("Type \\h for help, \\q to quit")

	reader := bufio.NewReader(os.Stdin)
	var multiLineQuery strings.Builder
	inMultiLine := false

	for {
		if inMultiLine {
			fmt.Print("... ")
		} else {
			fmt.Print("elasticsearch> ")
		}

		line, err := reader.ReadString('\n')
		if err != nil {
			if err == io.EOF {
				fmt.Println("\nBye!")
				return
			}
			fmt.Printf("Error reading input: %v\n", err)
			continue
		}

		line = strings.TrimSpace(line)

		// Handle special commands
		if !inMultiLine && strings.HasPrefix(line, "\\") {
			switch line {
			case "\\h", "\\help":
				printHelp()
			case "\\q", "\\quit", "\\exit":
				fmt.Println("Bye!")
				return
			case "\\c", "\\clear":
				clearScreen()
			case "\\l", "\\indices":
				listIndices()
			case "\\i", "\\info":
				showClusterInfo()
			case "\\health":
				showClusterHealth()
			default:
				fmt.Printf("Unknown command: %s\n", line)
			}
			continue
		}

		// Handle multi-line queries
		if inMultiLine {
			multiLineQuery.WriteString(line)
			multiLineQuery.WriteString(" ")
			if strings.HasSuffix(line, ";") {
				query := strings.TrimSuffix(multiLineQuery.String(), ";")
				query = strings.TrimSpace(query)
				inMultiLine = false
				multiLineQuery.Reset()
				executeCommand(query)
			}
		} else if line != "" {
			if strings.HasSuffix(line, ";") {
				query := strings.TrimSuffix(line, ";")
				executeCommand(query)
			} else {
				multiLineQuery.WriteString(line)
				multiLineQuery.WriteString(" ")
				inMultiLine = true
			}
		}
	}
}

func printHelp() {
	fmt.Println("\nElasticsearch CLI Commands:")
	fmt.Println("  \\h, \\help      Show this help message")
	fmt.Println("  \\q, \\quit      Exit the CLI")
	fmt.Println("  \\c, \\clear     Clear the screen")
	fmt.Println("  \\l, \\indices   List all indices")
	fmt.Println("  \\i, \\info      Show cluster info")
	fmt.Println("  \\health        Show cluster health")
	fmt.Println("\nAPI Commands (end with semicolon):")
	fmt.Println("  GET /_cat/indices;")
	fmt.Println("  GET /{index};")
	fmt.Println("  PUT /{index} {\"settings\": {...}, \"mappings\": {...}};")
	fmt.Println("  DELETE /{index};")
	fmt.Println("  POST /{index}/_doc {\"field\": \"value\"};")
	fmt.Println("  GET /{index}/_search {\"query\": {...}};")
	fmt.Println("\nExamples:")
	fmt.Println("  PUT /test_index {\"settings\": {\"number_of_shards\": 1}};")
	fmt.Println("  GET /test_index;")
	fmt.Println("  POST /test_index/_doc {\"title\": \"Test Document\"};")
	fmt.Println("  GET /test_index/_search {\"query\": {\"match_all\": {}}};")
	fmt.Println()
}

func clearScreen() {
	fmt.Print("\033[H\033[2J")
}

func listIndices() {
	resp, err := makeRequest("GET", "/_cat/indices?format=json", nil)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	result := gjson.Parse(resp)
	if !result.IsArray() {
		fmt.Println("No indices found")
		return
	}

	table := tablewriter.NewWriter(os.Stdout)
	table.SetHeader([]string{"Health", "Status", "Index", "Docs Count", "Store Size", "Pri Shards"})

	result.ForEach(func(key, value gjson.Result) bool {
		health := value.Get("health").String()
		status := value.Get("status").String()
		index := value.Get("index").String()
		docsCount := value.Get("docs.count").String()
		storeSize := value.Get("store.size").String()
		priShards := value.Get("pri").String()

		table.Append([]string{health, status, index, docsCount, storeSize, priShards})
		return true
	})

	table.Render()
}

func showClusterInfo() {
	resp, err := makeRequest("GET", "/", nil)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	result := gjson.Parse(resp)

	fmt.Println("\nCluster Information:")
	fmt.Printf("Name: %s\n", result.Get("name").String())
	fmt.Printf("Cluster Name: %s\n", result.Get("cluster_name").String())
	fmt.Printf("Cluster UUID: %s\n", result.Get("cluster_uuid").String())
	fmt.Printf("Version: %s\n", result.Get("version.number").String())
	fmt.Printf("Build Type: %s\n", result.Get("version.build_type").String())
	fmt.Printf("Build Hash: %s\n", result.Get("version.build_hash").String())
	fmt.Println()
}

func showClusterHealth() {
	resp, err := makeRequest("GET", "/_cluster/health", nil)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	result := gjson.Parse(resp)

	fmt.Println("\nCluster Health:")
	fmt.Printf("Cluster Name: %s\n", result.Get("cluster_name").String())
	fmt.Printf("Status: %s\n", result.Get("status").String())
	fmt.Printf("Number of Nodes: %d\n", result.Get("number_of_nodes").Int())
	fmt.Printf("Number of Data Nodes: %d\n", result.Get("number_of_data_nodes").Int())
	fmt.Printf("Active Primary Shards: %d\n", result.Get("active_primary_shards").Int())
	fmt.Printf("Active Shards: %d\n", result.Get("active_shards").Int())
	fmt.Printf("Relocating Shards: %d\n", result.Get("relocating_shards").Int())
	fmt.Printf("Initializing Shards: %d\n", result.Get("initializing_shards").Int())
	fmt.Printf("Unassigned Shards: %d\n", result.Get("unassigned_shards").Int())
	fmt.Println()
}

func executeCommand(command string) {
	start := time.Now()

	parts := strings.SplitN(command, " ", 3)
	if len(parts) < 2 {
		fmt.Println("Invalid command format. Use: METHOD /path [body]")
		return
	}

	method := strings.ToUpper(parts[0])
	path := parts[1]
	var body []byte

	if len(parts) == 3 {
		body = []byte(parts[2])
	}

	resp, err := makeRequest(method, path, body)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	// Pretty print JSON response
	var prettyJSON bytes.Buffer
	if err := json.Indent(&prettyJSON, []byte(resp), "", "  "); err != nil {
		fmt.Println(resp)
	} else {
		fmt.Println(prettyJSON.String())
	}

	fmt.Printf("\nTime: %v\n", time.Since(start))
}

func makeRequest(method, path string, body []byte) (string, error) {
	url := fmt.Sprintf("http://%s:%s%s", host, port, path)

	var req *http.Request
	var err error

	if body != nil {
		req, err = http.NewRequest(method, url, bytes.NewBuffer(body))
		req.Header.Set("Content-Type", "application/json")
	} else {
		req, err = http.NewRequest(method, url, nil)
	}

	if err != nil {
		return "", err
	}

	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	if resp.StatusCode >= 400 {
		return string(respBody), fmt.Errorf("HTTP %d: %s", resp.StatusCode, resp.Status)
	}

	return string(respBody), nil
}
