package utility

import (
	"github.com/gogf/gf/v2/errors/gerror"
)

// Scanner 是一个简单的字节流读取器
type Scanner struct {
	data []byte // 原始数据
	idx  int    // 当前读取位置
}

// New 创建一个新的 Scanner
func New(data []byte) *Scanner {
	return &Scanner{
		data: data,
		idx:  0,
	}
}

// IsEmpty 判断是否已读到结尾
func (s *Scanner) IsEmpty() bool {
	return s.idx >= len(s.data)
}

// Reset 允许将 scanner 复用为新的输入
func (s *Scanner) Reset(data []byte) {
	s.data = data
	s.idx = 0
}

// Next 读取 size 字节
func (s *Scanner) Next(size int) ([]byte, error) {
	if s.idx+size > len(s.data) {
		return s.data[s.idx:], gerror.Newf(
			"读取失败：剩余字节不足（剩余：%d，请求：%d，位置：%d）",
			len(s.data)-s.idx, size, s.idx,
		)
	}
	start := s.idx
	s.idx += size
	return s.data[start:s.idx], nil
}

// NextByte 获取1个字节
func (s *Scanner) NextByte() (byte, error) {
	b, err := s.Next(1)
	if err != nil {
		return 0, err
	}
	return b[0], nil
}

// Next2Bytes 获取2个字节
func (s *Scanner) Next2Bytes() ([]byte, error) {
	return s.Next(2)
}

// Next4Bytes 获取4个字节
func (s *Scanner) Next4Bytes() ([]byte, error) {
	return s.Next(4)
}

// Next5Bytes 获取5个字节
func (s *Scanner) Next5Bytes() ([]byte, error) {
	return s.Next(5)
}

// LastNBytes 获取最后 n 个字节
func (s *Scanner) LastNBytes(n int) ([]byte, error) {
	length := len(s.data)
	if n > length {
		return nil, gerror.Newf("请求字节数 %d 大于数据长度 %d", n, length)
	}
	return s.data[length-n:], nil
}
