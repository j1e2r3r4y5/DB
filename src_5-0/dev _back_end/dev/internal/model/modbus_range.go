package model

type ModbusRange struct {
	SlaveAddr  int    `json:"slaveAddr"`
	ModbusType int    `json:"modbusType"`
	StartAddr  int    `json:"startAddr"`
	Length     int    `json:"length"`
	VarCount   int    `json:"varCount"`
	IsOptimal  bool   `json:"isOptimal"`
}

type RangeOptimizationResult struct {
	Ranges           []ModbusRange `json:"ranges"`
	TotalVars        int           `json:"totalVars"`
	TotalConfigBytes int           `json:"totalConfigBytes"`
	TotalDataCache   int           `json:"totalDataCacheBytes"`
	MqttConfigCount  int           `json:"mqttConfigCount"`
	MqttDataCount    int           `json:"mqttDataCountEstimate"`
	IsWithinLimit    bool          `json:"isWithinLimit"`
	LimitReason      string        `json:"limitReason,omitempty"`
}

type StorageLimit struct {
	MaxConfigBytes     int `json:"maxConfigBytes"`
	MaxDataCacheBytes int `json:"maxDataCacheBytes"`
	MaxRangeCount     int `json:"maxRangeCount"`
	MaxMqttConfigCount int `json:"maxMqttConfigCount"`
}

type StoragePreset struct {
	Name        string       `json:"name"`
	Description string       `json:"description"`
	TypicalMCU  string       `json:"typicalMCU"`
	Limit       StorageLimit `json:"limit"`
	MaxVars     int          `json:"maxVarsEstimate"`
}

const (
	PresetNameLow    = "low"
	PresetNameMedium = "medium"
	PresetNameHigh   = "high"
	PresetNameCustom = "custom"
)

var StoragePresets = []StoragePreset{
	{
		Name:        PresetNameLow,
		Description: "低配方案 - 适用于资源极度受限的MCU",
		TypicalMCU:  "STM8S (2KB RAM), N76E003 (1KB RAM)",
		Limit: StorageLimit{
			MaxConfigBytes:     128,
			MaxDataCacheBytes: 512,
			MaxRangeCount:     20,
			MaxMqttConfigCount: 5,
		},
		MaxVars: 30,
	},
	{
		Name:        PresetNameMedium,
		Description: "中等方案 - 适用于中等规模工业应用",
		TypicalMCU:  "STM32F103 (64KB RAM), STM32F401 (64KB RAM)",
		Limit: StorageLimit{
			MaxConfigBytes:     512,
			MaxDataCacheBytes: 4096,
			MaxRangeCount:     50,
			MaxMqttConfigCount: 10,
		},
		MaxVars: 150,
	},
	{
		Name:        PresetNameHigh,
		Description: "高配方案 - 适用于资源充裕的高端MCU",
		TypicalMCU:  "STM32F4 (256KB RAM), ESP32 (520KB RAM)",
		Limit: StorageLimit{
			MaxConfigBytes:     2048,
			MaxDataCacheBytes: 16384,
			MaxRangeCount:     100,
			MaxMqttConfigCount: 20,
		},
		MaxVars: 500,
	},
}

type DataCacheEntry struct {
	SlaveAddr  int    `json:"slaveAddr"`
	ModbusType int    `json:"modbusType"`
	StartAddr  int    `json:"startAddr"`
	Length     int    `json:"length"`
	ByteOffset int    `json:"byteOffset"`
}

type OptimizedConfig struct {
	Ranges        []ModbusRange              `json:"ranges"`
	DataCacheMap  map[string]DataCacheEntry `json:"dataCacheMap"`
	RangeIndexMap map[string]int            `json:"rangeIndexMap"`
}

type ParetoSolution struct {
	Ranges              []ModbusRange `json:"ranges"`
	ConfigMessageBytes int           `json:"configMessageBytes"`
	DataMessageBytes   int           `json:"dataMessageBytes"`
	TotalMessageBytes  int           `json:"totalMessageBytes"`
	RangeCount         int           `json:"rangeCount"`
	DataPacketCount    int           `json:"dataPacketCount"`
}

type ParetoResult struct {
	Solutions    []ParetoSolution `json:"solutions"`
	BestByStorage *ParetoSolution `json:"bestByStorage"`
	BestByMqtt    *ParetoSolution `json:"bestByMqtt"`
	BestByTotal   *ParetoSolution `json:"bestByTotal"`
	StorageLimit StorageLimit    `json:"storageLimit"`
}

const (
	ModbusTypeCoil         = 1
	ModbusTypeDiscreteInput = 2
	ModbusTypeHoldingReg   = 3
	ModbusTypeInputReg     = 4

	MaxBytesPerMqttPacket = 1024
	ConfigBytesPerRange   = 6

	MqttHeaderBytes  = 3
	MqttBodyMinBytes = 20
)
