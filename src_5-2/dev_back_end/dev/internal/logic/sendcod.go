package logic

import (
	"context"
	"dev/internal/model"
	"dev/internal/service"
	"fmt"
	"sort"

	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/os/gtime"
)

type sSend struct {
}

// interval 表示一个区间范围
type interval struct {
	start, end int
}

func init() {
	service.RegisterSendCod(NewSend())
}

func NewSend() *sSend {
	return &sSend{}
}

// ==========================================
// 数据配置优化器接口（预留）
// ==========================================

// DataConfigOptimizer 数据配置优化器
type DataConfigOptimizer interface {
	// Optimize 优化数据配置项
	Optimize(items []model.Entry) ([]model.Entry, *model.OptimizationResult, error)
}

// DefaultOptimizer 默认优化器（按站号+分区简单合并）
type DefaultOptimizer struct{}

// Optimize 实现默认优化逻辑
func (d *DefaultOptimizer) Optimize(items []model.Entry) ([]model.Entry, *model.OptimizationResult, error) {
	if len(items) == 0 {
		return items, &model.OptimizationResult{}, nil
	}

	start := gtime.Now()

	// 按站号+分区分组
	groupMap := make(map[string][]model.Entry)
	for _, item := range items {
		key := fmt.Sprintf("%d-%d", item.SlaveAddr, item.DataType)
		groupMap[key] = append(groupMap[key], item)
	}

	// 每组内合并连续地址
	result := make([]model.Entry, 0)
	for _, group := range groupMap {
		if len(group) == 0 {
			continue
		}
		merged := d.mergeGroup(group)
		result = append(result, merged...)
	}

	// 计算原始和优化后的payload
	originalPayload := computePayload(items)
	optimizedPayload := computePayload(result)
	savedBytes := originalPayload - optimizedPayload
	savedPercent := 0.0
	if originalPayload > 0 {
		savedPercent = float64(savedBytes) / float64(originalPayload) * 100
	}

	optResult := &model.OptimizationResult{
		OriginalPayload:   originalPayload,
		OptimizedPayload:  optimizedPayload,
		SavedBytes:        savedBytes,
		SavedPercent:      savedPercent,
		OriginalSegments:  len(items),
		OptimizedSegments: len(result),
		ExecutionTimeMs:   gtime.Now().Sub(start).Milliseconds(),
	}

	return result, optResult, nil
}

// mergeGroup 合并同一分组内的地址
// 逻辑：按地址排序 → 取最小起始地址和最大结束地址 → 合并成一条（与原方案1保持一致）
func (d *DefaultOptimizer) mergeGroup(items []model.Entry) []model.Entry {
	if len(items) <= 1 {
		return items
	}

	// 1. 收集所有起始地址
	addrs := make([]uint16, 0, len(items))
	for _, item := range items {
		addrs = append(addrs, item.StartAddr)
	}

	// 2. 按地址排序
	sort.Slice(addrs, func(i, j int) bool {
		return addrs[i] < addrs[j]
	})

	// 3. 计算：minAddr 和 maxAddr（考虑了每个item的length）
	minAddr := addrs[0]
	maxAddr := addrs[0]
	for _, item := range items {
		// 计算每个item的结束地址
		endAddr := item.StartAddr + item.Length - 1
		if endAddr > maxAddr {
			maxAddr = endAddr
		}
	}

	// 4. 计算总长度
	totalLen := maxAddr - minAddr + 1

	// 5. 返回合并后的条目
	return []model.Entry{{
		SlaveAddr: items[0].SlaveAddr,
		DataType:  items[0].DataType,
		StartAddr: minAddr,
		Length:    totalLen,
	}}
}

// ==========================================
// PayloadOptimizer 高级优化器（阶段三~五算法）
// ==========================================

type PayloadOptimizer struct{}

func NewPayloadOptimizer() *PayloadOptimizer {
	return &PayloadOptimizer{}
}

// Optimize 实现完整优化算法
func (p *PayloadOptimizer) Optimize(items []model.Entry) ([]model.Entry, *model.OptimizationResult, error) {
	if len(items) == 0 {
		return items, &model.OptimizationResult{}, nil
	}

	start := gtime.Now()
	g.Log().Infof(context.Background(), "[PayloadOptimizer] 开始优化，变量数: %d", len(items))

	// 阶段三：提取必须覆盖的集合
	mustBytes1, mustRegs4 := extractMustCover(items)
	step1 := gtime.Now()
	g.Log().Infof(context.Background(), "[PayloadOptimizer] 阶段三完成，耗时: %v，1区字节数: %d，4区寄存器数: %d", step1.Sub(start), len(mustBytes1), len(mustRegs4))

	// 阶段四：优化求解
	opt1 := computeOptions(mustBytes1, 192)  // 1区最大192字节
	opt4 := computeOptions(mustRegs4, 12288) // 4区最大12288寄存器
	step2 := gtime.Now()
	g.Log().Infof(context.Background(), "[PayloadOptimizer] 阶段四完成，耗时: %v", step2.Sub(step1))

	// 可行性检查
	if len(mustBytes1) > 0 && len(opt1) == 0 {
		return nil, nil, gerror.New("无法满足优化硬约束（1区）")
	}
	if len(mustRegs4) > 0 && len(opt4) == 0 {
		return nil, nil, gerror.New("无法满足优化硬约束（4区）")
	}

	// 组合枚举找最优
	bestK1 := 0
	bestK4 := 0
	bestPayload := -1
	bestTotalAddr := -1

	// K=0 只有在没有数据时才有意义，不允许有数据时选 K=0
	k1Candidates := []int{}
	if len(mustBytes1) == 0 {
		k1Candidates = append(k1Candidates, 0)
	}
	for k := range opt1 {
		k1Candidates = append(k1Candidates, k)
	}
	
	k4Candidates := []int{}
	if len(mustRegs4) == 0 {
		k4Candidates = append(k4Candidates, 0)
	}
	for k := range opt4 {
		k4Candidates = append(k4Candidates, k)
	}

	for _, k1 := range k1Candidates {
		for _, k4 := range k4Candidates {
			kTotal := k1 + k4
			if kTotal > 30 {
				continue
			}

			b1 := 0
			if k1 > 0 {
				b1 = opt1[k1]
			}
			r4 := 0
			if k4 > 0 {
				r4 = opt4[k4]
			}

			payload := 3 + 6*kTotal + b1 + 2*r4
			totalAddr := 8*b1 + r4

			if bestPayload == -1 ||
				payload < bestPayload ||
				(payload == bestPayload && totalAddr < bestTotalAddr) {
				bestPayload = payload
				bestTotalAddr = totalAddr
				bestK1 = k1
				bestK4 = k4
			}
		}
	}

	if bestPayload == -1 {
		return nil, nil, gerror.New("无法满足优化硬约束")
	}
	step3 := gtime.Now()
	g.Log().Infof(context.Background(), "[PayloadOptimizer] 最优解搜索完成，耗时: %v，最优K1: %d，K4: %d", step3.Sub(step2), bestK1, bestK4)

	// 阶段五：重构优化段
	byteBlocks := buildIntervals(mustBytes1, bestK1)
	regBlocks := buildIntervals(mustRegs4, bestK4)
	step4 := gtime.Now()
	g.Log().Infof(context.Background(), "[PayloadOptimizer] 阶段五完成，耗时: %v", step4.Sub(step3))

	// 转换为最终优化段
	result := make([]model.Entry, 0)
	slaveAddr := items[0].SlaveAddr // 使用第一个的从站地址

	// 1区段
	for _, block := range byteBlocks {
		startAddr := uint16(block.start * 8)
		length := uint16((block.end - block.start + 1) * 8)
		result = append(result, model.Entry{
			SlaveAddr: slaveAddr,
			DataType:  1,
			StartAddr: startAddr,
			Length:    length,
		})
	}

	// 4区段
	for _, block := range regBlocks {
		result = append(result, model.Entry{
			SlaveAddr: slaveAddr,
			DataType:  4,
			StartAddr: uint16(block.start),
			Length:    uint16(block.end - block.start + 1),
		})
	}

	// 计算原始payload（用默认优化器合并且已合并后的结果，即"同区同站合并"的05上报包长度）
	defaultOpt := &DefaultOptimizer{}
	_, defaultResult, _ := defaultOpt.Optimize(items)
	originalPayload := defaultResult.OptimizedPayload
	originalSegments := defaultResult.OptimizedSegments

	savedBytes := originalPayload - bestPayload
	savedPercent := 0.0
	if originalPayload > 0 {
		savedPercent = float64(savedBytes) / float64(originalPayload) * 100
	}

	totalTime := gtime.Now().Sub(start)
	g.Log().Infof(context.Background(), "[PayloadOptimizer] 优化完成，总耗时: %v", totalTime)

	optResult := &model.OptimizationResult{
		OriginalPayload:   originalPayload,
		OptimizedPayload:  bestPayload,
		SavedBytes:        savedBytes,
		SavedPercent:      savedPercent,
		OriginalSegments:  originalSegments,
		OptimizedSegments: len(result),
		ExecutionTimeMs:   totalTime.Milliseconds(),
	}

	return result, optResult, nil
}

// ==========================================
// 辅助函数
// ==========================================

func computePayload(items []model.Entry) int {
	if len(items) == 0 {
		return 0
	}

	K := len(items)
	B1 := 0
	R4 := 0

	for _, item := range items {
		if item.DataType == 1 {
			// 1区：计算字节数（向上取整）
			bits := int(item.Length)
			bytes := (bits + 7) / 8
			B1 += bytes
		} else if item.DataType == 4 {
			// 4区：计算寄存器数
			R4 += int(item.Length)
		}
	}

	return 3 + 6*K + B1 + 2*R4
}

func extractMustCover(items []model.Entry) ([]int, []int) {
	byteIntervals := make([]interval, 0)
	regIntervals := make([]interval, 0)

	for _, item := range items {
		if item.DataType == 1 {
			// 1区bit地址转字节索引
			startBit := int(item.StartAddr)
			endBit := startBit + int(item.Length) - 1
			startByte := startBit / 8
			endByte := endBit / 8

			g.Log().Infof(context.Background(), "[extractMustCover] 处理1区变量，startBit:%d, endBit:%d, startByte:%d, endByte:%d", 
				startBit, endBit, startByte, endByte)
			
			byteIntervals = append(byteIntervals, interval{startByte, endByte})
		} else if item.DataType == 4 {
			// 4区寄存器
			startReg := int(item.StartAddr)
			endReg := startReg + int(item.Length) - 1

			g.Log().Infof(context.Background(), "[extractMustCover] 处理4区变量，startReg:%d, endReg:%d", 
				startReg, endReg)
			
			regIntervals = append(regIntervals, interval{startReg, endReg})
		}
	}

	// 合并区间并展开为独立的点
	mustBytes1 := mergeAndExpand(byteIntervals)
	mustRegs4 := mergeAndExpand(regIntervals)

	g.Log().Infof(context.Background(), "[extractMustCover] 完成，1区字节数:%d, 4区寄存器数:%d", 
		len(mustBytes1), len(mustRegs4))

	return mustBytes1, mustRegs4
}

// 合并区间，然后展开为单个点数组
func mergeAndExpand(intervals []interval) []int {
	if len(intervals) == 0 {
		return []int{}
	}

	// 按起始位置排序
	sort.Slice(intervals, func(i, j int) bool {
		return intervals[i].start < intervals[j].start
	})

	// 合并重叠或相邻的区间
	merged := []interval{intervals[0]}
	for i := 1; i < len(intervals); i++ {
		last := &merged[len(merged)-1]
		if intervals[i].start <= last.end+1 {
			// 重叠或相邻，合并
			if intervals[i].end > last.end {
				last.end = intervals[i].end
			}
		} else {
			// 不重叠，添加新区间
			merged = append(merged, intervals[i])
		}
	}

	// 展开为单个点（使用安全的方式）
	result := make([]int, 0)
	totalCount := 0
	for _, iv := range merged {
		count := iv.end - iv.start + 1
		if count <= 0 || count > 20000 {
			// 安全限制，防止范围过大或无效
			g.Log().Warningf(context.Background(), "[mergeAndExpand] 跳过过大的区间，start:%d, end:%d, count:%d", 
				iv.start, iv.end, count)
			continue
		}
		totalCount += count
		if totalCount > 50000 {
			// 全局安全限制
			g.Log().Warningf(context.Background(), "[mergeAndExpand] 全局限制，已处理 %d 个点，停止添加", totalCount)
			break
		}
		for i := iv.start; i <= iv.end; i++ {
			result = append(result, i)
		}
	}

	g.Log().Infof(context.Background(), "[mergeAndExpand] 完成，合并后 %d 个区间，展开为 %d 个点", 
		len(merged), len(result))
	return result
}

func computeOptions(points []int, maxLen int) map[int]int {
	result := make(map[int]int)

	if len(points) == 0 {
		return result
	}

	// 计算相邻点间隙
	type gapInfo struct {
		gap int
		idx int
	}
	gaps := make([]gapInfo, 0, len(points)-1)
	for i := 0; i < len(points)-1; i++ {
		gap := points[i+1] - points[i] - 1
		gaps = append(gaps, gapInfo{gap: gap, idx: i})
	}

	// 按间隙升序排列
	sort.Slice(gaps, func(i, j int) bool {
		return gaps[i].gap < gaps[j].gap
	})

	// 前缀和
	prefix := make([]int, len(gaps)+1)
	for i := 0; i < len(gaps); i++ {
		prefix[i+1] = prefix[i] + gaps[i].gap
	}

	// 对 K 从 1 开始
	n := len(points)
	maxK := min(n, 30)
	for K := 1; K <= maxK; K++ {
		var totalLen int
		if K >= n {
			totalLen = n
		} else {
			r := n - K
			totalLen = n + prefix[r]
		}
		if totalLen <= maxLen {
			result[K] = totalLen
		}
	}

	return result
}

func buildIntervals(points []int, K int) []interval {
	if len(points) == 0 {
		return nil
	}

	// K=0 表示不合并，全部按单个段处理
	if K >= len(points) || K == 0 {
		blocks := make([]interval, 0, len(points))
		for _, p := range points {
			blocks = append(blocks, interval{start: p, end: p})
		}
		return blocks
	}

	// 计算间隙（带索引）
	type gapInfo struct {
		gap int
		idx int
	}
	gaps := make([]gapInfo, 0, len(points)-1)
	for i := 0; i < len(points)-1; i++ {
		gap := points[i+1] - points[i] - 1
		gaps = append(gaps, gapInfo{gap: gap, idx: i})
	}

	// 按间隙降序排列
	sort.Slice(gaps, func(i, j int) bool {
		return gaps[i].gap > gaps[j].gap
	})

	// 取前 K-1 个间隙作为分割点
	splitIndices := make([]int, 0)
	if K > 1 && len(gaps) > 0 {
		numSplits := K - 1
		if numSplits > len(gaps) {
			numSplits = len(gaps)
		}
		for i := 0; i < numSplits; i++ {
			splitIndices = append(splitIndices, gaps[i].idx)
		}
	}

	// 分割点排序
	sort.Ints(splitIndices)

	// 构建块
	blocks := make([]interval, 0)
	prev := 0
	for _, idx := range splitIndices {
		blocks = append(blocks, interval{
			start: points[prev],
			end:   points[idx],
		})
		prev = idx + 1
	}
	blocks = append(blocks, interval{
		start: points[prev],
		end:   points[len(points)-1],
	})

	return blocks
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// ==========================================
// 协议编码函数
// ==========================================

// encodeModuleConfig 编码模组配置（功能码02）
// 协议: 0x02 + SendMode(1byte) + ConfigData(2bytes,大端) + Baud(1byte)
func encodeModuleConfig(req *model.Func02Request) ([]byte, error) {
	if req == nil {
		return nil, gerror.New("模组配置请求不能为空")
	}

	buf := make([]byte, 0, 5)
	// 功能码
	buf = append(buf, 0x02)
	// 发送模式
	buf = append(buf, req.SendMode)
	// 配置数据（大端）
	buf = append(buf, byte(req.ConfigData>>8), byte(req.ConfigData&0xFF))
	// 波特率
	buf = append(buf, req.BaudRate)

	return buf, nil
}

// encodeDataConfig 编码数据配置（功能码04）
// 协议: 0x04 + TotalLen(2bytes,大端) + 循环Entry列表
// 空配置: 0x04 + 0x00 + 0x03（总长度=3，无数据项）
func encodeDataConfig(entries []model.Entry) ([]byte, error) {
	buf := make([]byte, 0)
	// 功能码
	buf = append(buf, 0x04)
	// 计算报文总长度：1(功能码) + 2(长度) + len(entries)*6
	totalLen := 3 + len(entries)*6
	buf = append(buf, byte(totalLen>>8), byte(totalLen&0xFF))

	// 每个数据项
	for _, entry := range entries {
		buf = append(buf, entry.SlaveAddr)
		buf = append(buf, entry.DataType)
		buf = append(buf, byte(entry.StartAddr>>8), byte(entry.StartAddr&0xFF))
		buf = append(buf, byte(entry.Length>>8), byte(entry.Length&0xFF))
	}

	return buf, nil
}

// encodeQueryConfig 编码查询数据配置（功能码03）
// 协议: 0x03
func encodeQueryConfig() []byte {
	return []byte{0x03}
}

// encodeRemoteWrite 编码远程置数（功能码06）
// 协议: 0x06 + DataType(1byte) + StartAddr(2bytes,大端) + Quantity(2bytes,大端) + Values(...)
func encodeRemoteWrite(req *model.Func06Request) ([]byte, error) {
	if req == nil {
		return nil, gerror.New("远程置数请求不能为空")
	}

	buf := make([]byte, 0)
	// 功能码
	buf = append(buf, 0x06)
	// 数据类型
	buf = append(buf, req.DataType)
	// 起始地址（大端）
	buf = append(buf, byte(req.StartAddr>>8), byte(req.StartAddr&0xFF))
	// 数量（大端）
	buf = append(buf, byte(req.Quantity>>8), byte(req.Quantity&0xFF))
	// 值
	buf = append(buf, req.Values...)

	return buf, nil
}

// ==========================================
// 服务实现
// ==========================================

// SendModuleConfig 下发模组配置
func (s *sSend) SendModuleConfig(ctx context.Context, req *model.ModbusRequest) error {
	if req == nil || req.Func02 == nil {
		return gerror.New("模组配置请求无效")
	}
	if req.DevSerial == "" {
		return gerror.New("设备序列号不能为空")
	}

	g.Log().Info(ctx, "下发模组配置", "DevSerial", req.DevSerial, "SendMode", req.Func02.SendMode)

	// 编码协议
	payload, err := encodeModuleConfig(req.Func02)
	if err != nil {
		return err
	}

	// 发送
	topic := fmt.Sprintf("/dtu/%s/down", req.DevSerial)
	return service.Mqtt().PublishBytes(topic, payload)
}

// SendDataConfig 下发数据配置
func (s *sSend) SendDataConfig(ctx context.Context, req *model.ModbusRequest) (*model.OptimizationResult, string, error) {
	if req == nil || req.Func04 == nil {
		return nil, "", gerror.New("数据配置请求无效")
	}
	if req.DevSerial == "" {
		return nil, "", gerror.New("设备序列号不能为空")
	}

	g.Log().Info(ctx, "下发数据配置", "DevSerial", req.DevSerial, "Count", len(req.Func04.Entries))

	// ----------------------------
	// 优化阶段（优先使用 PayloadOptimizer，失败回退到 DefaultOptimizer）
	// ----------------------------
	var optimized []model.Entry
	var optResult *model.OptimizationResult
	var optimizerUsed string

	// 先尝试使用 PayloadOptimizer（高级优化）
	payloadOptimizer := NewPayloadOptimizer()
	var optErr error
	optimized, optResult, optErr = payloadOptimizer.Optimize(req.Func04.Entries)

	if optErr == nil {
		optimizerUsed = "PayloadOptimizer"
		g.Log().Infof(ctx, "[SendDataConfig] 使用优化器: %s", optimizerUsed)
		g.Log().Infof(ctx, "  原始 payload: %d 字节, 段数: %d", optResult.OriginalPayload, optResult.OriginalSegments)
		g.Log().Infof(ctx, "  优化后 payload: %d 字节, 段数: %d", optResult.OptimizedPayload, optResult.OptimizedSegments)
		g.Log().Infof(ctx, "  节省: %d 字节 (%.2f%%)", optResult.SavedBytes, optResult.SavedPercent)
	} else {
		// PayloadOptimizer 失败，回退到 DefaultOptimizer
		g.Log().Warningf(ctx, "[SendDataConfig] PayloadOptimizer 失败: %v，回退到 DefaultOptimizer", optErr)
		defaultOptimizer := &DefaultOptimizer{}
		optimized, optResult, optErr = defaultOptimizer.Optimize(req.Func04.Entries)
		if optErr == nil {
			optimizerUsed = "DefaultOptimizer"
			g.Log().Infof(ctx, "[SendDataConfig] 使用优化器: %s", optimizerUsed)
			g.Log().Infof(ctx, "  原始 payload: %d 字节, 段数: %d", optResult.OriginalPayload, optResult.OriginalSegments)
			g.Log().Infof(ctx, "  优化后 payload: %d 字节, 段数: %d", optResult.OptimizedPayload, optResult.OptimizedSegments)
			g.Log().Infof(ctx, "  节省: %d 字节 (%.2f%%)", optResult.SavedBytes, optResult.SavedPercent)
		} else {
			// 都失败，使用原始数据
			optimizerUsed = "RawData"
			g.Log().Errorf(ctx, "[SendDataConfig] 使用优化器: %s (所有优化器失败)", optimizerUsed)
			optimized = req.Func04.Entries
			optResult = nil
		}
	}

	// 编码协议
	payload, err := encodeDataConfig(optimized)
	if err != nil {
		return nil, "", err
	}

	// 发送
	topic := fmt.Sprintf("/dtu/%s/down", req.DevSerial)
	if req.Func04.Scope == "sandbox" {
		topic = fmt.Sprintf("/dtu/%s/sandbox/down", req.DevSerial)
	}
	err = service.Mqtt().PublishBytes(topic, payload)
	if err != nil {
		return nil, "", err
	}

	return optResult, optimizerUsed, nil
}

// QueryDataConfig 查询数据配置
func (s *sSend) QueryDataConfig(ctx context.Context, devSerial string) error {
	if devSerial == "" {
		return gerror.New("设备序列号不能为空")
	}

	g.Log().Info(ctx, "查询数据配置", "DevSerial", devSerial)

	// 编码协议
	payload := encodeQueryConfig()

	// 发送
	topic := fmt.Sprintf("/dtu/%s/down", devSerial)
	return service.Mqtt().PublishBytes(topic, payload)
}

// RemoteWrite 远程置数
func (s *sSend) RemoteWrite(ctx context.Context, req *model.ModbusRequest) error {
	if req == nil || req.Func06 == nil {
		return gerror.New("远程置数请求无效")
	}
	if req.DevSerial == "" {
		return gerror.New("设备序列号不能为空")
	}

	g.Log().Info(ctx, "远程置数", "DevSerial", req.DevSerial, "StartAddr", req.Func06.StartAddr)

	// 编码协议
	payload, err := encodeRemoteWrite(req.Func06)
	if err != nil {
		return err
	}

	// 发送
	topic := fmt.Sprintf("/dtu/%s/down", req.DevSerial)
	return service.Mqtt().PublishBytes(topic, payload)
}
