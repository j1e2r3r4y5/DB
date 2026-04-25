package logic

import (
	"dev/internal/model"
	"fmt"
	"sort"
	"strconv"
)

type ModbusRangeOptimizer struct {
	limit model.StorageLimit
}

func NewModbusRangeOptimizer(limit model.StorageLimit) *ModbusRangeOptimizer {
	if limit.MaxConfigBytes == 0 {
		limit.MaxConfigBytes = 256
	}
	if limit.MaxDataCacheBytes == 0 {
		limit.MaxDataCacheBytes = 4096
	}
	if limit.MaxRangeCount == 0 {
		limit.MaxRangeCount = 50
	}
	if limit.MaxMqttConfigCount == 0 {
		limit.MaxMqttConfigCount = 10
	}
	return &ModbusRangeOptimizer{limit: limit}
}

func (o *ModbusRangeOptimizer) Optimize(variables []*model.Variables) *model.RangeOptimizationResult {
	if len(variables) == 0 {
		return &model.RangeOptimizationResult{
			Ranges:           []model.ModbusRange{},
			TotalVars:        0,
			TotalConfigBytes: 0,
			TotalDataCache:   0,
			MqttConfigCount:  0,
			MqttDataCount:    0,
			IsWithinLimit:    true,
		}
	}

	grouped := o.groupBySlaveAndType(variables)
	var optimalRanges []model.ModbusRange
	totalVars := 0
	totalConfigBytes := 0
	totalDataCacheBytes := 0

	for _, vars := range grouped {
		sort.Slice(vars, func(i, j int) bool {
			return vars[i].ModbusAddr < vars[j].ModbusAddr
		})

		solutions := o.computeParetoForGroup(vars)
		var ranges []model.ModbusRange
		if len(solutions) > 0 {
			ranges = solutions[0].Ranges
		}
		for i := range ranges {
			ranges[i].IsOptimal = true
		}

		optimalRanges = append(optimalRanges, ranges...)
		totalVars += len(vars)

		for _, r := range ranges {
			configBytes := model.ConfigBytesPerRange
			totalConfigBytes += configBytes

			dataCacheBytes := o.calculateDataCacheBytes(r)
			totalDataCacheBytes += dataCacheBytes
		}
	}

	configCount := len(optimalRanges)
	dataCount := o.estimateMqttDataCount(optimalRanges)

	isWithinLimit := true
	limitReason := ""

	if totalConfigBytes > o.limit.MaxConfigBytes {
		isWithinLimit = false
		limitReason = fmt.Sprintf("配置字节数超限: %d > %d", totalConfigBytes, o.limit.MaxConfigBytes)
	} else if totalDataCacheBytes > o.limit.MaxDataCacheBytes {
		isWithinLimit = false
		limitReason = fmt.Sprintf("数据缓存超限: %d > %d", totalDataCacheBytes, o.limit.MaxDataCacheBytes)
	} else if configCount > o.limit.MaxRangeCount {
		isWithinLimit = false
		limitReason = fmt.Sprintf("区间数量超限: %d > %d", configCount, o.limit.MaxRangeCount)
	}

	return &model.RangeOptimizationResult{
		Ranges:           optimalRanges,
		TotalVars:        totalVars,
		TotalConfigBytes: totalConfigBytes,
		TotalDataCache:   totalDataCacheBytes,
		MqttConfigCount:  configCount,
		MqttDataCount:    dataCount,
		IsWithinLimit:    isWithinLimit,
		LimitReason:      limitReason,
	}
}

func (o *ModbusRangeOptimizer) GetParetoSolutions(variables []*model.Variables) *model.ParetoResult {
	if len(variables) == 0 {
		return &model.ParetoResult{
			Solutions:    []model.ParetoSolution{},
			StorageLimit: o.limit,
		}
	}

	grouped := o.groupBySlaveAndType(variables)
	var allSolutions []model.ParetoSolution

	for _, vars := range grouped {
		sort.Slice(vars, func(i, j int) bool {
			return vars[i].ModbusAddr < vars[j].ModbusAddr
		})

		solutions := o.computeParetoForGroup(vars)
		allSolutions = append(allSolutions, solutions...)
	}

	sort.Slice(allSolutions, func(i, j int) bool {
		return allSolutions[i].TotalMessageBytes < allSolutions[j].TotalMessageBytes
	})

	var bestByStorage, bestByMqtt, bestByTotal *model.ParetoSolution

	if len(allSolutions) > 0 {
		bestByTotal = &allSolutions[0]

		bestByStorage = &allSolutions[0]
		for i := 1; i < len(allSolutions); i++ {
			if allSolutions[i].ConfigMessageBytes < bestByStorage.ConfigMessageBytes {
				bestByStorage = &allSolutions[i]
			}
		}

		bestByMqtt = &allSolutions[0]
		for i := 1; i < len(allSolutions); i++ {
			if allSolutions[i].DataPacketCount < bestByMqtt.DataPacketCount {
				bestByMqtt = &allSolutions[i]
			}
		}
	}

	return &model.ParetoResult{
		Solutions:    allSolutions,
		BestByStorage: bestByStorage,
		BestByMqtt:   bestByMqtt,
		BestByTotal:  bestByTotal,
		StorageLimit:  o.limit,
	}
}

func (o *ModbusRangeOptimizer) computeParetoForGroup(variables []*model.Variables) []model.ParetoSolution {
	if len(variables) == 0 {
		return []model.ParetoSolution{}
	}

	if len(variables) == 1 {
		v := variables[0]
		length := o.calculateVariableLength(v)
		rangeResult := model.ModbusRange{
			SlaveAddr:  v.ModbusDevice,
			ModbusType: parseModbusType(v.ModbusType),
			StartAddr:  v.ModbusAddr,
			Length:     length,
			VarCount:   1,
		}

		configBytes := o.calculateConfigMessageBytes([]model.ModbusRange{rangeResult})
		dataBytes, pktCount := o.calculateDataMessageBytes([]model.ModbusRange{rangeResult})

		return []model.ParetoSolution{
			{
				Ranges:              []model.ModbusRange{rangeResult},
				ConfigMessageBytes:  configBytes,
				DataMessageBytes:    dataBytes,
				TotalMessageBytes:   configBytes + dataBytes,
				RangeCount:          1,
				DataPacketCount:     pktCount,
			},
		}
	}

	addrMap := make(map[int]*model.Variables)
	addrList := make([]int, 0, len(variables))
	varLengths := make([]int, len(variables))

	for i, v := range variables {
		addrMap[v.ModbusAddr] = v
		addrList = append(addrList, v.ModbusAddr)
		varLengths[i] = o.calculateVariableLength(v)
	}
	sort.Ints(addrList)

	for i, addr := range addrList {
		varLengths[i] = o.calculateVariableLength(addrMap[addr])
	}

	maxRanges := o.limit.MaxRangeCount
	if maxRanges <= 0 {
		maxRanges = 50
	}
	if maxRanges > len(variables) {
		maxRanges = len(variables)
	}

	allContiguous := o.checkAllContiguous(addrList)
	if allContiguous {
		totalLength := 0
		for _, l := range varLengths {
			totalLength += l
		}
		rangeResult := model.ModbusRange{
			SlaveAddr:  variables[0].ModbusDevice,
			ModbusType: parseModbusType(variables[0].ModbusType),
			StartAddr:  addrList[0],
			Length:     totalLength,
			VarCount:   len(variables),
		}

		configBytes := o.calculateConfigMessageBytes([]model.ModbusRange{rangeResult})
		dataBytes, pktCount := o.calculateDataMessageBytes([]model.ModbusRange{rangeResult})

		return []model.ParetoSolution{
			{
				Ranges:              []model.ModbusRange{rangeResult},
				ConfigMessageBytes:  configBytes,
				DataMessageBytes:    dataBytes,
				TotalMessageBytes:   configBytes + dataBytes,
				RangeCount:          1,
				DataPacketCount:     pktCount,
			},
		}
	}

	prefixSum := make([]int, len(addrList)+1)
	for i := 0; i < len(addrList); i++ {
		prefixSum[i+1] = prefixSum[i] + varLengths[i]
	}

	type splitKey struct {
		start int
		end   int
	}
	splitCostMap := make(map[splitKey]struct {
		configBytes int
		dataBytes  int
		pktCount   int
	})

	computeSplitCost := func(start, end int) (configBytes, dataBytes, pktCount int) {
		key := splitKey{start, end}
		if cost, ok := splitCostMap[key]; ok {
			return cost.configBytes, cost.dataBytes, cost.pktCount
		}

		rangeLength := prefixSum[end] - prefixSum[start]
		modbusType := parseModbusType(variables[0].ModbusType)

		configBytes = model.ConfigBytesPerRange

		dataBytes = o.calculateDataBytesForRange(rangeLength, modbusType)

		totalPayload := dataBytes + model.MqttHeaderBytes + model.MqttBodyMinBytes
		if totalPayload <= model.MaxBytesPerMqttPacket {
			pktCount = 1
		} else {
			pktCount = (totalPayload + model.MaxBytesPerMqttPacket - 1) / model.MaxBytesPerMqttPacket
		}

		splitCostMap[key] = struct {
			configBytes int
			dataBytes  int
			pktCount   int
		}{configBytes, dataBytes, pktCount}

		return configBytes, dataBytes, pktCount
	}

	type dpEntry struct {
		splits             []int
		configBytes       int
		dataBytes         int
		pktCount          int
		totalMessageBytes int
	}

	dp := make(map[int]map[int]*dpEntry)

	for i := 1; i <= len(addrList); i++ {
		dp[i] = make(map[int]*dpEntry)

		for k := 1; k <= maxRanges && k <= i; k++ {
			bestEntry := &dpEntry{}

			for j := k - 1; j < i; j++ {
				var prevEntry *dpEntry
				if j == 0 {
					prevEntry = &dpEntry{
						splits:             []int{},
						configBytes:       0,
						dataBytes:         0,
						pktCount:          0,
						totalMessageBytes: 0,
					}
				} else {
					if prev, ok := dp[j][k-1]; ok {
						prevEntry = prev
					} else {
						continue
					}
				}

				cfgBytes, dataBytes, pktCount := computeSplitCost(j, i)

				totalCfg := prevEntry.configBytes + cfgBytes
				totalData := prevEntry.dataBytes + dataBytes
				totalPkt := prevEntry.pktCount + pktCount
				totalMsg := totalCfg + totalData

				newSplits := make([]int, len(prevEntry.splits)+1)
				copy(newSplits, prevEntry.splits)
				newSplits[len(newSplits)-1] = j

				entry := &dpEntry{
					splits:             newSplits,
					configBytes:       totalCfg,
					dataBytes:         totalData,
					pktCount:          totalPkt,
					totalMessageBytes: totalMsg,
				}

				if bestEntry.splits == nil || entry.totalMessageBytes < bestEntry.totalMessageBytes {
					bestEntry = entry
				}
			}

			if bestEntry.splits != nil {
				dp[i][k] = bestEntry
			}
		}
	}

	solutionMap := make(map[int]*model.ParetoSolution)

	for i := 1; i <= len(addrList); i++ {
		for k := 1; k <= maxRanges; k++ {
			if entry, ok := dp[i][k]; ok && entry.splits != nil {
				if existing, exists := solutionMap[k]; !exists || entry.totalMessageBytes < existing.TotalMessageBytes {
					solutionMap[k] = &model.ParetoSolution{
						Ranges:              o.buildRangesFromSplits(entry.splits, i, addrList, prefixSum, variables),
						ConfigMessageBytes:  entry.configBytes,
						DataMessageBytes:    entry.dataBytes,
						TotalMessageBytes:   entry.totalMessageBytes,
						RangeCount:          k,
						DataPacketCount:     entry.pktCount,
					}
				}
			}
		}
	}

	var paretoSolutions []model.ParetoSolution
	for k := 1; k <= maxRanges; k++ {
		if sol, ok := solutionMap[k]; ok && sol != nil {
			if o.isParetoOptimal(sol, solutionMap, maxRanges) {
				paretoSolutions = append(paretoSolutions, *sol)
			}
		}
	}

	if len(paretoSolutions) == 0 {
		for k := 1; k <= maxRanges; k++ {
			if sol, ok := solutionMap[k]; ok && sol != nil {
				paretoSolutions = append(paretoSolutions, *sol)
			}
		}
	}

	sort.Slice(paretoSolutions, func(i, j int) bool {
		return paretoSolutions[i].RangeCount < paretoSolutions[j].RangeCount
	})

	return paretoSolutions
}

func (o *ModbusRangeOptimizer) isParetoOptimal(sol *model.ParetoSolution, allSolutions map[int]*model.ParetoSolution, maxRanges int) bool {
	for k := 1; k <= maxRanges; k++ {
		other := allSolutions[k]
		if other == nil || other == sol {
			continue
		}
		if other.ConfigMessageBytes <= sol.ConfigMessageBytes &&
			other.DataPacketCount <= sol.DataPacketCount &&
			(other.ConfigMessageBytes < sol.ConfigMessageBytes || other.DataPacketCount < sol.DataPacketCount) {
			return false
		}
	}
	return true
}

func (o *ModbusRangeOptimizer) buildRangesFromSplits(splits []int, endIndex int, addrList []int, prefixSum []int, variables []*model.Variables) []model.ModbusRange {
	var ranges []model.ModbusRange

	prevSplit := 0
	for _, split := range splits {
		if split > prevSplit {
			rangeAddrs := addrList[prevSplit:split]
			rangeLength := prefixSum[split] - prefixSum[prevSplit]
			ranges = append(ranges, model.ModbusRange{
				SlaveAddr:  variables[0].ModbusDevice,
				ModbusType: parseModbusType(variables[0].ModbusType),
				StartAddr:  rangeAddrs[0],
				Length:     rangeLength,
				VarCount:   len(rangeAddrs),
			})
		}
		prevSplit = split
	}

	if endIndex > prevSplit {
		rangeAddrs := addrList[prevSplit:endIndex]
		rangeLength := prefixSum[endIndex] - prefixSum[prevSplit]
		ranges = append(ranges, model.ModbusRange{
			SlaveAddr:  variables[0].ModbusDevice,
			ModbusType: parseModbusType(variables[0].ModbusType),
			StartAddr:  rangeAddrs[0],
			Length:     rangeLength,
			VarCount:   len(rangeAddrs),
		})
	}

	return ranges
}

func (o *ModbusRangeOptimizer) calculateVariableLength(v *model.Variables) int {
	length := 1
	if v.DataLen != "" {
		fmt.Sscanf(v.DataLen, "%d", &length)
		if length <= 0 {
			length = 1
		}
	}
	return length
}

func (o *ModbusRangeOptimizer) calculateDataBytesForRange(length int, modbusType int) int {
	switch modbusType {
	case model.ModbusTypeCoil, model.ModbusTypeDiscreteInput:
		return (length + 7) / 8
	case model.ModbusTypeHoldingReg, model.ModbusTypeInputReg:
		return length * 2
	default:
		return length * 2
	}
}

func (o *ModbusRangeOptimizer) calculateDataCacheBytes(r model.ModbusRange) int {
	return o.calculateDataBytesForRange(r.Length, r.ModbusType)
}

func (o *ModbusRangeOptimizer) calculateConfigMessageBytes(ranges []model.ModbusRange) int {
	if len(ranges) == 0 {
		return 0
	}

	cfgPayloadBytes := len(ranges) * model.ConfigBytesPerRange
	totalBytes := cfgPayloadBytes + model.MqttHeaderBytes + model.MqttBodyMinBytes

	if totalBytes <= model.MaxBytesPerMqttPacket {
		return totalBytes
	}
	return ((totalBytes + model.MaxBytesPerMqttPacket - 1) / model.MaxBytesPerMqttPacket) * model.MaxBytesPerMqttPacket
}

func (o *ModbusRangeOptimizer) calculateDataMessageBytes(ranges []model.ModbusRange) (totalBytes int, packetCount int) {
	if len(ranges) == 0 {
		return 0, 0
	}

	dataBytes := 0
	for _, r := range ranges {
		dataBytes += o.calculateDataCacheBytes(r)
	}

	totalBytes = dataBytes + model.MqttHeaderBytes + model.MqttBodyMinBytes
	if totalBytes <= model.MaxBytesPerMqttPacket {
		return totalBytes, 1
	}

	packetCount = (totalBytes + model.MaxBytesPerMqttPacket - 1) / model.MaxBytesPerMqttPacket
	return packetCount * model.MaxBytesPerMqttPacket, packetCount
}

func (o *ModbusRangeOptimizer) checkAllContiguous(addrList []int) bool {
	for i := 1; i < len(addrList); i++ {
		if addrList[i]-addrList[i-1] != 1 {
			return false
		}
	}
	return true
}

func (o *ModbusRangeOptimizer) estimateMqttDataCount(ranges []model.ModbusRange) int {
	if len(ranges) == 0 {
		return 0
	}

	dataBytes := 0
	for _, r := range ranges {
		dataBytes += o.calculateDataCacheBytes(r)
	}

	totalBytes := dataBytes + model.MqttHeaderBytes + model.MqttBodyMinBytes
	if totalBytes <= model.MaxBytesPerMqttPacket {
		return 1
	}
	return (totalBytes + model.MaxBytesPerMqttPacket - 1) / model.MaxBytesPerMqttPacket
}

func (o *ModbusRangeOptimizer) groupBySlaveAndType(variables []*model.Variables) map[string][]*model.Variables {
	groups := make(map[string][]*model.Variables)
	for _, v := range variables {
		key := fmt.Sprintf("%d_%s", v.ModbusDevice, v.ModbusType)
		groups[key] = append(groups[key], v)
	}
	return groups
}

func parseModbusType(mt string) int {
	switch mt {
	case "1", "coils", "Coil":
		return model.ModbusTypeCoil
	case "2", "discrete", "DiscreteInput":
		return model.ModbusTypeDiscreteInput
	case "3", "holding", "HoldingRegister":
		return model.ModbusTypeHoldingReg
	case "4", "input", "InputRegister":
		return model.ModbusTypeInputReg
	default:
		val, err := strconv.Atoi(mt)
		if err != nil {
			return model.ModbusTypeHoldingReg
		}
		return val
	}
}

func (o *ModbusRangeOptimizer) BuildOptimizedConfig(variables []*model.Variables) *model.OptimizedConfig {
	result := o.Optimize(variables)
	if len(result.Ranges) == 0 {
		return &model.OptimizedConfig{
			Ranges:       []model.ModbusRange{},
			DataCacheMap: make(map[string]model.DataCacheEntry),
			RangeIndexMap: make(map[string]int),
		}
	}

	dataCacheMap := make(map[string]model.DataCacheEntry)
	rangeIndexMap := make(map[string]int)
	currentByteOffset := 0

	for i, r := range result.Ranges {
		key := fmt.Sprintf("%d_%d_%d", r.SlaveAddr, r.ModbusType, r.StartAddr)
		rangeIndexMap[key] = i

		lengthBytes := o.calculateDataCacheBytes(r)

		dataCacheMap[key] = model.DataCacheEntry{
			SlaveAddr:  r.SlaveAddr,
			ModbusType: r.ModbusType,
			StartAddr:  r.StartAddr,
			Length:     r.Length,
			ByteOffset: currentByteOffset,
		}
		currentByteOffset += lengthBytes
	}

	return &model.OptimizedConfig{
		Ranges:       result.Ranges,
		DataCacheMap: dataCacheMap,
		RangeIndexMap: rangeIndexMap,
	}
}

func (o *ModbusRangeOptimizer) GetRangeByVariable(v *model.Variables, config *model.OptimizedConfig) *model.ModbusRange {
	modbusType := parseModbusType(v.ModbusType)
	for _, r := range config.Ranges {
		if r.SlaveAddr == v.ModbusDevice &&
			r.ModbusType == modbusType &&
			v.ModbusAddr >= r.StartAddr &&
			v.ModbusAddr < r.StartAddr+r.Length {
			return &r
		}
	}
	return nil
}

func (o *ModbusRangeOptimizer) CalculateStorageSavings(originalVars, optimizedRanges []model.ModbusRange) map[string]int {
	originalConfigBytes := len(originalVars) * model.ConfigBytesPerRange
	optimizedConfigBytes := len(optimizedRanges) * model.ConfigBytesPerRange

	originalDataCache := 0
	for _, r := range originalVars {
		originalDataCache += o.calculateDataCacheBytes(r)
	}

	optimizedDataCache := 0
	for _, r := range optimizedRanges {
		optimizedDataCache += o.calculateDataCacheBytes(r)
	}

	return map[string]int{
		"configBytesSaved": originalConfigBytes - optimizedConfigBytes,
		"dataCacheSaved":   originalDataCache - optimizedDataCache,
		"mqttPacketsSaved": (originalConfigBytes - optimizedConfigBytes) / model.MaxBytesPerMqttPacket,
	}
}

func BuildDefaultStorageLimit() model.StorageLimit {
	return model.StorageLimit{
		MaxConfigBytes:     256,
		MaxDataCacheBytes:  4096,
		MaxRangeCount:      50,
		MaxMqttConfigCount: 10,
	}
}

func OptimizeModbusVariables(variables []*model.Variables, limit *model.StorageLimit) *model.RangeOptimizationResult {
	if limit == nil {
		defaultLimit := BuildDefaultStorageLimit()
		limit = &defaultLimit
	}
	optimizer := NewModbusRangeOptimizer(*limit)
	return optimizer.Optimize(variables)
}

func BuildModbusOptimizedConfig(variables []*model.Variables, limit *model.StorageLimit) *model.OptimizedConfig {
	if limit == nil {
		defaultLimit := BuildDefaultStorageLimit()
		limit = &defaultLimit
	}
	optimizer := NewModbusRangeOptimizer(*limit)
	return optimizer.BuildOptimizedConfig(variables)
}

func GetModbusParetoSolutions(variables []*model.Variables, limit *model.StorageLimit) *model.ParetoResult {
	if limit == nil {
		defaultLimit := BuildDefaultStorageLimit()
		limit = &defaultLimit
	}
	optimizer := NewModbusRangeOptimizer(*limit)
	return optimizer.GetParetoSolutions(variables)
}
