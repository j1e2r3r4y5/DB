package logic

import (
	"dev/internal/model"
	"testing"

	"github.com/gogf/gf/v2/test/gtest"
)

// ==========================================
// 辅助函数测试
// ==========================================

func TestComputePayload(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 空输入
		t.Assert(computePayload([]model.Entry{}), 0)

		// 单个1区变量
		items1 := []model.Entry{{SlaveAddr: 1, DataType: 1, StartAddr: 100, Length: 1}}
		t.Assert(computePayload(items1), 3+6*1+1) // K=1, B1=1, R4=0

		// 单个4区变量
		items2 := []model.Entry{{SlaveAddr: 1, DataType: 4, StartAddr: 100, Length: 2}}
		t.Assert(computePayload(items2), 3+6*1+2*2) // K=1, B1=0, R4=2

		// 混合
		items3 := []model.Entry{
			{SlaveAddr: 1, DataType: 1, StartAddr: 100, Length: 8},
			{SlaveAddr: 1, DataType: 4, StartAddr: 200, Length: 5},
		}
		t.Assert(computePayload(items3), 3+6*2+1+2*5) // K=2, B1=1, R4=5
	})
}

func TestMergeAndExpand(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 空输入
		result := mergeAndExpand([]interval{})
		t.AssertEQ(len(result), 0)

		// 单个区间
		result = mergeAndExpand([]interval{{start: 5, end: 8}})
		t.AssertEQ(len(result), 4)
		t.AssertEQ(result, []int{5, 6, 7, 8})

		// 不重叠的多个区间
		result = mergeAndExpand([]interval{{start: 1, end: 3}, {start: 6, end: 8}})
		t.AssertEQ(result, []int{1, 2, 3, 6, 7, 8})

		// 重叠区间
		result = mergeAndExpand([]interval{{start: 1, end: 5}, {start: 3, end: 7}})
		t.AssertEQ(result, []int{1, 2, 3, 4, 5, 6, 7})

		// 相邻区间
		result = mergeAndExpand([]interval{{start: 1, end: 3}, {start: 4, end: 6}})
		t.AssertEQ(result, []int{1, 2, 3, 4, 5, 6})
	})
}

func TestExtractMustCover(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 空输入
		b1, r4 := extractMustCover([]model.Entry{})
		t.AssertEQ(len(b1), 0)
		t.AssertEQ(len(r4), 0)

		// 单个1区变量（1字节）
		items := []model.Entry{{SlaveAddr: 1, DataType: 1, StartAddr: 0, Length: 8}}
		b1, r4 = extractMustCover(items)
		t.AssertEQ(len(b1), 1)
		t.AssertEQ(b1, []int{0})

		// 1区跨2字节
		items = []model.Entry{{SlaveAddr: 1, DataType: 1, StartAddr: 7, Length: 2}}
		b1, r4 = extractMustCover(items)
		t.AssertEQ(len(b1), 2)
		t.AssertEQ(b1, []int{0, 1})

		// 单个4区变量
		items = []model.Entry{{SlaveAddr: 1, DataType: 4, StartAddr: 100, Length: 3}}
		b1, r4 = extractMustCover(items)
		t.AssertEQ(len(r4), 3)
		t.AssertEQ(r4, []int{100, 101, 102})

		// 混合
		items = []model.Entry{
			{SlaveAddr: 1, DataType: 1, StartAddr: 0, Length: 8},
			{SlaveAddr: 1, DataType: 4, StartAddr: 100, Length: 2},
		}
		b1, r4 = extractMustCover(items)
		t.AssertEQ(len(b1), 1)
		t.AssertEQ(len(r4), 2)
	})
}

func TestComputeOptions(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 空输入
		opts := computeOptions([]int{}, 100)
		t.AssertEQ(len(opts), 0)

		// 单个点
		opts = computeOptions([]int{100}, 100)
		t.AssertEQ(opts[1], 1)

		// 连续点（无间隙）
		points := []int{1, 2, 3, 4, 5}
		opts = computeOptions(points, 100)
		t.AssertEQ(opts[1], 5) // K=1，一个区间覆盖全部

		// 离散点（有间隙）
		points = []int{1, 2, 4, 5} // 间隙在2和4之间（gap=1）
		opts = computeOptions(points, 100)
		t.Assert(opts[1] >= 4, true) // K=1，合并间隙
		t.Assert(opts[2] >= 2, true) // K=2，在间隙处分割
	})
}

func TestBuildIntervals(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 空输入
		blocks := buildIntervals([]int{}, 1)
		t.AssertEQ(len(blocks), 0)

		// 单个点
		blocks = buildIntervals([]int{100}, 1)
		t.AssertEQ(len(blocks), 1)
		t.AssertEQ(blocks[0], interval{start: 100, end: 100})

		// K >= 点数量
		blocks = buildIntervals([]int{1, 2, 3}, 10)
		t.AssertEQ(len(blocks), 3)

		// 连续点，K=1
		blocks = buildIntervals([]int{1, 2, 3, 4, 5}, 1)
		t.AssertEQ(len(blocks), 1)
		t.AssertEQ(blocks[0], interval{start: 1, end: 5})

		// 离散点，K=2
		blocks = buildIntervals([]int{1, 2, 4, 5, 7, 8}, 2)
		t.AssertEQ(len(blocks), 2)
	})
}

// ==========================================
// DefaultOptimizer 测试
// ==========================================

func TestDefaultOptimizer_Empty(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		opt := &DefaultOptimizer{}
		result, res, err := opt.Optimize([]model.Entry{})
		t.AssertNil(err)
		t.AssertEQ(len(result), 0)
		t.AssertNE(res, nil)
	})
}

func TestDefaultOptimizer_Single(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		opt := &DefaultOptimizer{}
		items := []model.Entry{{SlaveAddr: 1, DataType: 4, StartAddr: 100, Length: 2}}
		result, res, err := opt.Optimize(items)
		t.AssertNil(err)
		t.AssertEQ(len(result), 1)
		t.Assert(res.SavedBytes >= 0, true)
	})
}

func TestDefaultOptimizer_Merge(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		opt := &DefaultOptimizer{}
		items := []model.Entry{
			{SlaveAddr: 1, DataType: 4, StartAddr: 100, Length: 2},
			{SlaveAddr: 1, DataType: 4, StartAddr: 102, Length: 3},
		}
		result, res, err := opt.Optimize(items)
		t.AssertNil(err)
		t.AssertEQ(len(result), 1)
		t.AssertEQ(result[0].StartAddr, uint16(100))
		t.AssertEQ(result[0].Length, uint16(5))
		t.Assert(res.SavedPercent > 0, true)
	})
}

// ==========================================
// PayloadOptimizer 测试
// ==========================================

func TestPayloadOptimizer_Empty(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		opt := NewPayloadOptimizer()
		result, res, err := opt.Optimize([]model.Entry{})
		t.AssertNil(err)
		t.AssertEQ(len(result), 0)
		t.AssertNE(res, nil)
	})
}

func TestPayloadOptimizer_Single4区(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		opt := NewPayloadOptimizer()
		items := []model.Entry{{SlaveAddr: 1, DataType: 4, StartAddr: 100, Length: 1}}
		result, res, err := opt.Optimize(items)
		t.AssertNil(err)
		t.AssertEQ(len(result), 1)
		t.Assert(res.OptimizedSegments >= 1, true)
	})
}

func TestPayloadOptimizer_Single1区(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		opt := NewPayloadOptimizer()
		items := []model.Entry{{SlaveAddr: 1, DataType: 1, StartAddr: 0, Length: 8}}
		result, _, err := opt.Optimize(items)
		t.AssertNil(err)
		t.AssertEQ(len(result), 1)
	})
}

func TestPayloadOptimizer_Consecutive(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		opt := NewPayloadOptimizer()
		items := []model.Entry{
			{SlaveAddr: 1, DataType: 4, StartAddr: 100, Length: 1},
			{SlaveAddr: 1, DataType: 4, StartAddr: 101, Length: 1},
			{SlaveAddr: 1, DataType: 4, StartAddr: 102, Length: 1},
		}
		_, res, err := opt.Optimize(items)
		t.AssertNil(err)
		t.Assert(res.OptimizedSegments <= res.OriginalSegments, true)
		t.Assert(res.SavedBytes >= 0, true)
	})
}

func TestPayloadOptimizer_Mixed(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		opt := NewPayloadOptimizer()
		items := []model.Entry{
			{SlaveAddr: 1, DataType: 1, StartAddr: 0, Length: 8},
			{SlaveAddr: 1, DataType: 4, StartAddr: 100, Length: 2},
		}
		result, res, err := opt.Optimize(items)
		t.AssertNil(err)
		t.AssertNE(result, nil)
		t.AssertNE(res, nil)
	})
}

func TestPayloadOptimizer_WithGaps(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		opt := NewPayloadOptimizer()
		items := []model.Entry{
			{SlaveAddr: 1, DataType: 4, StartAddr: 100, Length: 1},
			{SlaveAddr: 1, DataType: 4, StartAddr: 103, Length: 1},
			{SlaveAddr: 1, DataType: 4, StartAddr: 106, Length: 1},
		}
		result, _, err := opt.Optimize(items)
		t.AssertNil(err)
		t.AssertNE(result, nil)
	})
}

// ==========================================
// 编码函数测试
// ==========================================

func TestEncodeModuleConfig(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		req := &model.Func02Request{SendMode: 1, ConfigData: 0x1234, BaudRate: 5}
		payload, err := encodeModuleConfig(req)
		t.AssertNil(err)
		t.AssertEQ(len(payload), 5)
		t.AssertEQ(payload[0], byte(0x02)) // 功能码
		t.AssertEQ(payload[1], byte(1))    // 发送模式
		t.AssertEQ(payload[2], byte(0x12)) // ConfigData 高字节
		t.AssertEQ(payload[3], byte(0x34)) // ConfigData 低字节
		t.AssertEQ(payload[4], byte(5))    // 波特率
	})

	gtest.C(t, func(t *gtest.T) {
		payload, err := encodeModuleConfig(nil)
		t.AssertNE(err, nil)
		t.AssertEQ(len(payload), 0)
	})
}

func TestEncodeDataConfig(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		// 空配置
		payload, err := encodeDataConfig([]model.Entry{})
		t.AssertNil(err)
		t.AssertEQ(len(payload), 3) // 0x04 + 0x00 + 0x03
		t.AssertEQ(payload[0], byte(0x04))

		// 单个条目
		items := []model.Entry{{SlaveAddr: 1, DataType: 4, StartAddr: 100, Length: 2}}
		payload, err = encodeDataConfig(items)
		t.AssertNil(err)
		t.AssertEQ(len(payload), 3+6*1)
	})
}

func TestEncodeRemoteWrite(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		req := &model.Func06Request{
			DataType:  4,
			StartAddr: 100,
			Quantity:  2,
			Values:    []byte{0x12, 0x34, 0x56, 0x78},
		}
		payload, err := encodeRemoteWrite(req)
		t.AssertNil(err)
		t.AssertEQ(len(payload), 6+4)
		t.AssertEQ(payload[0], byte(0x06))
	})

	gtest.C(t, func(t *gtest.T) {
		payload, err := encodeRemoteWrite(nil)
		t.AssertNE(err, nil)
		t.AssertEQ(len(payload), 0)
	})
}

func TestEncodeQueryConfig(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		payload := encodeQueryConfig()
		t.AssertEQ(len(payload), 1)
		t.AssertEQ(payload[0], byte(0x03))
	})
}

// ==========================================
// 边界条件测试
// ==========================================

func TestMin(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		t.AssertEQ(min(3, 5), 3)
		t.AssertEQ(min(5, 3), 3)
		t.AssertEQ(min(-1, 1), -1)
		t.AssertEQ(min(0, 0), 0)
	})
}

func TestPayloadOptimizer_KLimit(t *testing.T) {
	gtest.C(t, func(t *gtest.T) {
		opt := NewPayloadOptimizer()
		items := []model.Entry{}
		for i := 0; i < 50; i++ {
			items = append(items, model.Entry{
				SlaveAddr: 1,
				DataType:  4,
				StartAddr: uint16(100 + i*10),
				Length:    1,
			})
		}
		result, res, err := opt.Optimize(items)
		t.AssertNil(err)
		t.AssertNE(result, nil)
		t.Assert(res.OptimizedSegments <= 30, true) // K不超过30限制
	})
}

// ==========================================
// 性能基准测试（可选）
// ==========================================

func BenchmarkPayloadOptimizer(b *testing.B) {
	opt := NewPayloadOptimizer()
	items := []model.Entry{}
	for i := 0; i < 50; i++ {
		items = append(items, model.Entry{
			SlaveAddr: 1,
			DataType:  4,
			StartAddr: uint16(100 + i*5),
			Length:    2,
		})
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _, _ = opt.Optimize(items)
	}
}

func BenchmarkDefaultOptimizer(b *testing.B) {
	opt := &DefaultOptimizer{}
	items := []model.Entry{}
	for i := 0; i < 50; i++ {
		items = append(items, model.Entry{
			SlaveAddr: 1,
			DataType:  4,
			StartAddr: uint16(100 + i*5),
			Length:    2,
		})
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _, _ = opt.Optimize(items)
	}
}
