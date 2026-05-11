export function parseLine(line) {
    const parts = line.trim().split(/\s+/)
    if (parts.length < 4) return null
    const idx = parseInt(parts[0], 10)
    const partition = parseInt(parts[1], 10)
    const address = parseInt(parts[2], 10)
    const length = parseInt(parts[3], 10)
    if (isNaN(idx) || isNaN(partition) || isNaN(address) || isNaN(length)) return null
    return { idx, partition, address, length }
}

export function buildPreview(lines) {
    const items = []
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i]
        if (!line.trim() || line.trim().startsWith('#')) continue
        const parsed = parseLine(line)
        if (parsed) items.push({ lineNumber: i + 1, ...parsed })
    }
    return items
}
