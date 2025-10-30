package common

import "time"

var StartTime = time.Now().Unix() // unit: second
var Version = "v0.0.10"           // this hard coding will be replaced automatically when building, no need to manually change

type ModelInfo struct {
	Model string
	ID    string
	Type  string
}

// 创建映射表（假设用 model 名称作为 key）
var ModelRegistry = map[string]ModelInfo{
	"claude-3-5-sonnet-20241022":              {"claude-3-5-sonnet-20241022", "f44e280a-7914-43ca-a25d-ecfcc5d48d09", "chat"},
	"gemini-2.0-flash-001":                    {"gemini-2.0-flash-001", "7a55108b-b997-4cff-a72f-5aa83beee918", "chat"},
	"chatgpt-4o-latest-20250326":              {"chatgpt-4o-latest-20250326", "9513524d-882e-4350-b31e-e4584440c2c8", "chat"},
	"llama-4-maverick-03-26-experimental":     {"llama-4-maverick-03-26-experimental", "49bd7403-c7fd-4d91-9829-90a91906ad6c", "chat"},
	"gpt-4.1-2025-04-14":                      {"gpt-4.1-2025-04-14", "14e9311c-94d2-40c2-8c54-273947e208b0", "chat"},
	"qwq-32b":                                 {"qwq-32b", "885976d3-d178-48f5-a3f4-6e13e0718872", "chat"},
	"grok-3-preview-02-24":                    {"grok-3-preview-02-24", "551ba709-049c-4883-b4aa-8df24174e676", "chat"},
	"claude-3-7-sonnet-20250219-thinking-32k": {"claude-3-7-sonnet-20250219-thinking-32k", "be98fcfd-345c-4ae1-9a82-a19123ebf1d2", "chat"},
	"gpt-4.1-mini-2025-04-14":                 {"gpt-4.1-mini-2025-04-14", "6a5437a7-c786-467b-b701-17b0bc8c8231", "chat"},
	"grok-3-mini-beta":                        {"grok-3-mini-beta", "7699c8d4-0742-42f9-a117-d10e84688dab", "chat"},
	"o3-2025-04-16":                           {"o3-2025-04-16", "cb0f1e24-e8e9-4745-aabc-b926ffde7475", "chat"},
	"claude-3-7-sonnet-20250219":              {"claude-3-7-sonnet-20250219", "c5a11495-081a-4dc6-8d9a-64a4fd6f7bbc", "chat"},
	"claude-opus-4-20250514":                  {"claude-opus-4-20250514", "ee116d12-64d6-48a8-88e5-b2d06325cdd2", "chat"},
	"claude-sonnet-4-20250514":                {"claude-3-7-sonnet-20250219", "ac44dd10-0666-451c-b824-386ccfea7bcc", "chat"},
	"claude-3-5-haiku-20241022":               {"claude-3-5-haiku-20241022", "f6fbf06c-532c-4c8a-89c7-f3ddcfb34bd1", "chat"},
	"o4-mini-2025-04-16":                      {"o4-mini-2025-04-16", "f1102bbf-34ca-468f-a9fc-14bcf63f315b", "chat"},
	"o3-mini":                                 {"o3-mini", "c680645e-efac-4a81-b0af-da16902b2541", "chat"},
	"gemma-3-27b-it":                          {"gemma-3-27b-it", "789e245f-eafe-4c72-b563-d135e93988fc", "chat"},
	"gemini-2.5-flash-preview-04-17":          {"gemini-2.5-flash-preview-04-17", "7fff29a7-93cc-44ab-b685-482c55ce4fa6", "chat"},
	"amazon.nova-pro-v1:0":                    {"amazon.nova-pro-v1:0", "a14546b5-d78d-4cf6-bb61-ab5b8510a9d6", "chat"},
	"command-a-03-2025":                       {"command-a-03-2025", "0f785ba1-efcb-472d-961e-69f7b251c7e3", "chat"},
	"mistral-medium-2505":                     {"mistral-medium-2505", "27b9f8c6-3ee1-464a-9479-a8b3c2a48fd4", "chat"},
	"deepseek-v3-0324":                        {"deepseek-v3-0324", "2f5253e4-75be-473c-bcfc-baeb3df0f8ad", "chat"},
	"qwen3-235b-a22b":                         {"qwen3-235b-a22b", "2595a594-fa54-4299-97cd-2d7380d21c80", "chat"},
	"qwen-max-2025-01-25":                     {"qwen-max-2025-01-25", "fe8003fc-2e5d-4a3f-8f07-c1cff7ba0159", "chat"},
	"llama-3.3-70b-instruct":                  {"llama-3.3-70b-instruct", "dcbd7897-5a37-4a34-93f1-76a24c7bb028", "chat"},
	"qwen3-30b-a3b":                           {"qwen3-30b-a3b", "9a066f6a-7205-4325-8d0b-d81cc4b049c0", "chat"},
	"llama-4-maverick-17b-128e-instruct":      {"llama-4-maverick-17b-128e-instruct", "b5ad3ab7-fc56-4ecd-8921-bd56b55c1159", "chat"},
	"gemini-2.5-pro-preview-05-06":            {"gemini-2.5-pro-preview-05-06", "0337ee08-8305-40c0-b820-123ad42b60cf", "chat"},

	"gemini-2.0-flash-preview-image-generation": {"gemini-2.0-flash-preview-image-generation", "69bbf7d4-9f44-447e-a868-abc4f7a31810", "image"},
	"imagen-3.0-generate-002":                   {"imagen-3.0-generate-002", "51ad1d79-61e2-414c-99e3-faeb64bb6b1b", "image"},
	"ideogram-v2":                               {"ideogram-v2", "34ee5a83-8d85-4d8b-b2c1-3b3413e9ed98", "image"},
	"gpt-image-1":                               {"gpt-image-1", "6e855f13-55d7-4127-8656-9168a9f4dcc0", "image"},
	"photon":                                    {"photon", "17e31227-36d7-4a7a-943a-7ebffa3a00eb", "image"},
	"dall-e-3":                                  {"dall-e-3", "bb97bc68-131c-4ea4-a59e-03a6252de0d2", "image"},
	"recraft-v3":                                {"recraft-v3", "b70ab012-18e7-4d6f-a887-574e05de6c20", "image"},
	"flux-1.1-pro":                              {"flux-1.1-pro", "9e8525b7-fe50-4e50-bf7f-ad1d3d205d3c", "image"},
}

// 通过 model 名称查询的方法
func GetModelInfo(modelName string) (ModelInfo, bool) {
	info, exists := ModelRegistry[modelName]
	return info, exists
}

func GetModelList() []string {
	var modelList []string
	for k := range ModelRegistry {
		modelList = append(modelList, k)
	}
	return modelList
}
